"""Evalue les outils AutoML sur le meme decoupage que la reference."""

import argparse
import json
import time
from importlib.metadata import version
from pathlib import Path

import mlflow
import pandas as pd
from mlflow.models import infer_signature
from sklearn.metrics import f1_score, precision_score, recall_score

from configuration import charger_configuration
from preparer import CIBLE, VARIABLES, lire_classeur, preparer, separer


def mesurer(y, predictions):
    return {
        "f1": float(f1_score(y, predictions, pos_label=1, zero_division=0)),
        "precision": float(precision_score(y, predictions, pos_label=1, zero_division=0)),
        "rappel": float(recall_score(y, predictions, pos_label=1, zero_division=0)),
    }


def versions(*packages):
    return [f"{package}=={version(package)}" for package in packages]


def entrainer_flaml(train, test, config, budget):
    from flaml import AutoML

    reglages = config["automl"]
    X_train = train[list(VARIABLES)]
    X_test = test[list(VARIABLES)]
    automate = AutoML(mlflow_logging=False)
    depart = time.perf_counter()
    automate.fit(
        X_train, train[CIBLE], task="classification", metric="f1",
        time_budget=budget, seed=config["donnees"]["graine"],
        n_jobs=reglages["threads"], verbose=0,
    )
    duree = time.perf_counter() - depart
    modele = automate.model.estimator
    metriques = mesurer(test[CIBLE], automate.predict(X_test))
    exemple = X_train.head(3)
    signature = infer_signature(exemple, modele.predict(exemple))
    options = dict(name="modele", input_example=exemple, signature=signature)
    paquet = type(modele).__module__.split(".")[0]
    if paquet == "lightgbm":
        import mlflow.lightgbm as flavor
    elif paquet == "xgboost":
        import mlflow.xgboost as flavor
    elif paquet == "catboost":
        import mlflow.catboost as flavor
    else:
        import mlflow.sklearn as flavor
        options.update(serialization_format="skops", skops_trusted_types=["sklearn.tree._tree.Tree"])
        paquet = "scikit-learn"
    options["pip_requirements"] = versions("mlflow", "pandas", "numpy", "scipy", paquet)
    if paquet == "scikit-learn":
        options["pip_requirements"] += versions("skops")
    info = flavor.log_model(modele, **options)
    return {
        "algorithme": automate.best_estimator, "budget_secondes": budget,
        "duree_secondes": duree, "modele_uri": info.model_uri, **metriques,
    }


def entrainer_h2o(train, test, config, classement):
    import h2o
    import mlflow.h2o as flavor
    from h2o.automl import H2OAutoML

    reglages = config["automl"]
    h2o.init(ip="127.0.0.1", port=reglages["port_h2o"],
             nthreads=reglages["threads"], max_mem_size=reglages["memoire_h2o"])
    h2o.no_progress()
    cadre_train = h2o.H2OFrame(train)
    cadre_train[CIBLE] = cadre_train[CIBLE].asfactor()
    modele = H2OAutoML(
        max_models=reglages["max_modeles_h2o"], seed=config["donnees"]["graine"],
        exclude_algos=reglages["algos_exclus_h2o"], sort_metric=reglages["classement_h2o"],
        project_name=config["suivi"]["experience"] + "-automl",
    )
    depart = time.perf_counter()
    modele.train(x=list(VARIABLES), y=CIBLE, training_frame=cadre_train)
    duree = time.perf_counter() - depart
    tableau = modele.leaderboard.as_data_frame()
    tableau.to_csv(classement, index=False)
    mlflow.log_artifact(str(classement))
    leader = modele.leader
    X_test = test[list(VARIABLES)]
    predictions = leader.predict(h2o.H2OFrame(X_test)).as_data_frame()
    metriques = mesurer(test[CIBLE], predictions["predict"].astype(int))
    exemple = X_test.head(3)
    signature = infer_signature(exemple, predictions.head(3))
    info = flavor.log_model(
        leader, name="modele", input_example=exemple, signature=signature,
        pip_requirements=versions("mlflow", "h2o", "pandas", "numpy"),
    )
    return {
        "algorithme": leader.algo, "modele_h2o": leader.model_id,
        "projet_h2o": modele.project_name, "classement": reglages["classement_h2o"],
        "score_classement": float(tableau.iloc[0][reglages["classement_h2o"].lower()]),
        "max_modeles": reglages["max_modeles_h2o"], "duree_secondes": duree,
        "modele_uri": info.model_uri, **metriques,
    }


def main(args):
    config = charger_configuration()
    suivi, reglages = config["suivi"], config["automl"]
    version_donnees = reglages["version_donnees"]
    preparees = preparer(lire_classeur(Path(suivi["sources"][version_donnees])))
    train, test = separer(preparees, config["donnees"]["graine"], config["donnees"]["part_test"])
    mlflow.set_tracking_uri(suivi["uri"])
    mlflow.set_experiment(suivi["experience"])
    budget = reglages["budgets_flaml"][args.essai - 1] if args.outil == "flaml" else None
    nom = f"d-flaml-{budget}s" if args.outil == "flaml" else "d-h2o-automl"
    with mlflow.start_run(run_name=nom) as run:
        if args.outil == "flaml":
            resultat = entrainer_flaml(train, test, config, budget)
        else:
            resultat = entrainer_h2o(train, test, config, args.classement)
        resultat.update(outil=args.outil, run_id=run.info.run_id,
                        version_donnees=version_donnees, n_train=len(train), n_test=len(test))
        mlflow.log_params({cle: valeur for cle, valeur in resultat.items()
                           if cle not in ("f1", "precision", "rappel", "run_id")})
        mlflow.log_metrics({cle: resultat[cle] for cle in ("f1", "precision", "rappel")})
    texte = json.dumps(resultat, indent=2, ensure_ascii=False)
    args.sortie.write_text(texte + "\n", encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("outil", choices=("flaml", "h2o"))
    cli.add_argument("sortie", type=Path)
    cli.add_argument("--essai", type=int, choices=(1, 2))
    cli.add_argument("--classement", type=Path)
    args = cli.parse_args()
    if (args.outil == "flaml" and args.essai is None) or (args.outil == "h2o" and args.classement is None):
        cli.error("FLAML demande --essai et H2O demande --classement")
    main(args)
