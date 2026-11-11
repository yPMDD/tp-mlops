"""Enregistre les versions de reference et gere leurs alias."""

import argparse
import json
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow import MlflowClient

from configuration import charger_configuration
from medicament_personnel import selection_personnelle


def lire_json(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8-sig"))


def promouvoir(client: MlflowClient, config: dict, v1: dict, v2: dict):
    nom = config["suivi"]["modele_rf"]
    seuil = config["qualite"]["f1_min"]
    for run in (v1, v2):
        f1 = client.get_run(run["run_id"]).data.metrics["f1"]
        if f1 < seuil:
            raise ValueError(f"Enregistrement refuse pour {run['nom']} : F1 {f1:.6f} < {seuil}.")

    versions = {}
    for run in (v1, v2):
        donnees = run["version_donnees"]
        version = mlflow.register_model(run["modele_uri"], nom).version
        client.set_model_version_tag(nom, version, "version_donnees", donnees)
        versions[donnees] = version

    client.set_registered_model_alias(nom, "staging", versions["v1"])
    client.set_registered_model_alias(nom, "production", versions["v2"])
    production = client.get_model_version_by_alias(nom, "production")
    staging = client.get_model_version_by_alias(nom, "staging")
    medicament, entrees = selection_personnelle(config, production.tags["version_donnees"])
    uri = f"models:/{nom}@production"
    modele = mlflow.sklearn.load_model(uri)
    indice_classe_1 = list(modele.classes_).index(1)
    probabilite = float(modele.predict_proba(entrees)[0, indice_classe_1])
    return {
        "modele": nom,
        "versions": versions,
        "production": production.version,
        "staging": staging.version,
        "uri": uri,
        "medicament": medicament,
        "probabilite_classe_1": probabilite,
    }


def retour_arriere(client: MlflowClient, config: dict, preuve: dict):
    nom = config["suivi"]["modele_rf"]
    avant = client.get_model_version_by_alias(nom, "production").version
    client.set_registered_model_alias(nom, "production", preuve["versions"]["v1"])
    apres = client.get_model_version_by_alias(nom, "production")
    return {
        "modele": nom,
        "production_avant": avant,
        "production_apres": apres.version,
        "donnees_apres": apres.tags["version_donnees"],
        "uri": f"models:/{nom}@production",
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    sous_commandes = cli.add_subparsers(dest="action", required=True)
    promotion = sous_commandes.add_parser("promouvoir")
    promotion.add_argument("--v1", type=Path, required=True)
    promotion.add_argument("--runs-v2", type=Path, required=True)
    rollback = sous_commandes.add_parser("retour")
    rollback.add_argument("--preuve", type=Path, required=True)
    cli.add_argument("--sortie", type=Path, required=True)
    args = cli.parse_args()

    config = charger_configuration()
    mlflow.set_tracking_uri(config["suivi"]["uri"])
    client = MlflowClient()
    if args.action == "promouvoir":
        reference = next(
            r for r in lire_json(args.runs_v2)
            if r["algorithme"] == "foret" and r["profondeur"] == config["foret"]["profondeur"]
        )
        resultat = promouvoir(client, config, lire_json(args.v1), reference)
    else:
        resultat = retour_arriere(client, config, lire_json(args.preuve))
    texte = json.dumps(resultat, ensure_ascii=False, indent=2)
    args.sortie.write_text(texte + "\n", encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
