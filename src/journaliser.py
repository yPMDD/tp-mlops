"""Journalise un entrainement et son evaluation dans MLflow."""

import argparse
import hashlib
import json
from importlib.metadata import version as version_paquet
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from configuration import charger_configuration
from entrainer import entrainer_foret
from evaluer import mesurer
from preparer import CIBLE, VARIABLES, lire_classeur, preparer, separer


def journaliser(version_donnees: str, algorithme: str, profondeur: int | None) -> dict:
    config = charger_configuration()
    suivi = config["suivi"]
    donnees = config["donnees"]
    source = Path(suivi["sources"][version_donnees])
    preparees = preparer(lire_classeur(source))
    train, test = separer(preparees, donnees["graine"], donnees["part_test"])
    X = train[list(VARIABLES)]
    y = train[CIBLE]
    parametres = {
        "algorithme": algorithme,
        "version_donnees": version_donnees,
        "md5_donnees": hashlib.md5(source.read_bytes()).hexdigest(),
        "graine": donnees["graine"],
        "part_test": donnees["part_test"],
        "f1_min": config["qualite"]["f1_min"],
    }
    if algorithme == "foret":
        if profondeur is not None:
            config["foret"]["profondeur"] = profondeur
        parametres.update(config["foret"])
        nom = f"{version_donnees}-foret-p{config['foret']['profondeur']}"
    else:
        parametres["max_iter"] = suivi["max_iter_logistique"]
        nom = f"{version_donnees}-logistique"

    mlflow.set_tracking_uri(suivi["uri"])
    mlflow.set_experiment(suivi["experience"])
    with mlflow.start_run(run_name=nom) as run:
        if algorithme == "foret":
            modele = entrainer_foret(train, config)
        else:
            modele = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=suivi["max_iter_logistique"], random_state=donnees["graine"]),
            ).fit(X, y)
        metriques = mesurer(modele, test)
        exemple = X.head(3)
        signature = infer_signature(exemple, modele.predict(exemple))
        mlflow.log_params(parametres)
        mlflow.log_metrics(metriques)
        info = mlflow.sklearn.log_model(
            modele,
            name="modele",
            signature=signature,
            input_example=exemple,
            serialization_format="skops",
            skops_trusted_types=["sklearn.tree._tree.Tree"] if algorithme == "foret" else None,
            pip_requirements=[
                f"{paquet}=={version_paquet(paquet)}"
                for paquet in ("mlflow", "scikit-learn", "numpy", "scipy", "pandas", "skops")
            ],
        )
        return {
            "nom": nom,
            "run_id": run.info.run_id,
            "experiment_id": run.info.experiment_id,
            "modele_uri": info.model_uri,
            **parametres,
            **metriques,
        }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--version", choices=("reference", "v1", "v2"), required=True)
    cli.add_argument("--algorithme", choices=("foret", "logistique"), required=True)
    cli.add_argument("--profondeur", type=int)
    cli.add_argument("--sortie", type=Path)
    args = cli.parse_args()
    if args.algorithme == "logistique" and args.profondeur is not None:
        cli.error("--profondeur est reservee a la foret")
    version_donnees = charger_configuration()["donnees"]["version"] if args.version == "reference" else args.version
    resultat = journaliser(version_donnees, args.algorithme, args.profondeur)
    texte = json.dumps(resultat, indent=2, ensure_ascii=False)
    if args.sortie:
        args.sortie.parent.mkdir(parents=True, exist_ok=True)
        args.sortie.write_text(texte + "\n", encoding="utf-8")
    print(texte)
