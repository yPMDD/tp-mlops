"""Reentraine, controle et propose une foret au registre MLflow."""

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from prefect import flow, get_run_logger, task

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from configuration import charger_configuration
from entrainer import entrainer_foret
from evaluer import mesurer
from preparer import VARIABLES, lire_classeur, preparer, separer
from valider import valider


@task(name="lire-donnees")
def lire(source):
    chemin = Path(source)
    get_run_logger().info("Lecture de %s", chemin.as_posix())
    if not chemin.is_file():
        raise FileNotFoundError(f"Classeur introuvable : {source}")
    return lire_classeur(chemin)


@task(name="preparer")
def preparer_jeux(brut, donnees):
    valider(brut)
    return separer(preparer(brut), donnees["graine"], donnees["part_test"])


@task(name="entrainer")
def entrainer(jeux, config):
    return entrainer_foret(jeux[0], config)


@task(name="evaluer")
def evaluer(modele, jeux):
    scores = mesurer(modele, jeux[1])
    get_run_logger().info("F1 de classe 1 : %.6f", scores["f1"])
    return scores


@task(name="controler-qualite")
def controler(scores, seuil):
    if scores["f1"] < seuil:
        raise ValueError(f"Modele refuse : F1 {scores['f1']:.6f} < seuil {seuil:.2f}.")
    return scores


@task(name="enregistrer-staging")
def enregistrer(modele, jeux, scores, config, version_donnees):
    suivi = config["suivi"]
    mlflow.set_tracking_uri(suivi["uri"])
    mlflow.set_experiment(suivi["experience"])
    exemple = jeux[0][list(VARIABLES)].head(3)
    signature = infer_signature(exemple, modele.predict(exemple))
    with mlflow.start_run(run_name=f"prefect-{version_donnees}") as run:
        mlflow.log_params({**config["foret"], "version_donnees": version_donnees,
                           "graine": config["donnees"]["graine"]})
        mlflow.log_metrics(scores)
        info = mlflow.sklearn.log_model(
            modele, name="modele", signature=signature, input_example=exemple,
            serialization_format="skops", skops_trusted_types=["sklearn.tree._tree.Tree"],
        )
    version = mlflow.register_model(info.model_uri, suivi["modele_rf"]).version
    client = mlflow.MlflowClient()
    client.set_model_version_tag(suivi["modele_rf"], version, "version_donnees", version_donnees)
    client.set_registered_model_alias(suivi["modele_rf"], "staging", version)
    get_run_logger().info("Staging pointe vers la version %s.", version)
    return {"version_staging": version, "run_mlflow": run.info.run_id, **scores}


@flow(name="reentrainement-medicaments")
def reentrainement(profondeur: int | None = None, version_donnees: str | None = None):
    config = deepcopy(charger_configuration())
    reglages = config["orchestration"]
    version_donnees = version_donnees or reglages["version_donnees"]
    if profondeur is not None:
        config["foret"]["profondeur"] = profondeur
    source = config["suivi"]["sources"][version_donnees]
    brut = lire.with_options(retries=reglages["reessais"],
                             retry_delay_seconds=reglages["delai_reessai"]).submit(source)
    brut.result()
    jeux = preparer_jeux.submit(brut, config["donnees"])
    modele = entrainer.submit(jeux, config)
    scores = evaluer.submit(modele, jeux)
    valides = controler.submit(scores, config["qualite"]["f1_min"])
    valides.result()
    return enregistrer.submit(modele, jeux, valides, config, version_donnees).result()


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("sortie", type=Path)
    cli.add_argument("--profondeur", type=int)
    cli.add_argument("--version", choices=("v1", "v2"))
    args = cli.parse_args()
    state = reentrainement(args.profondeur, args.version, return_state=True)
    resultat = state.result(raise_on_failure=False)
    preuve = {"flow_run_id": str(state.state_details.flow_run_id),
              "etat": state.name, "message": state.message,
              "resultat": resultat if isinstance(resultat, dict) else str(resultat)}
    args.sortie.write_text(json.dumps(preuve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(preuve)
