"""Enregistre le meilleur AutoML et mesure les deux services MLflow."""

import argparse
import json
import statistics
import time
from pathlib import Path
from urllib.request import Request, urlopen

import mlflow

from configuration import charger_configuration
from medicament_personnel import selection_personnelle


def lire_json(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def enregistrer(config, rapports):
    candidat = max((lire_json(p) for p in rapports), key=lambda r: r["f1"])
    client = mlflow.MlflowClient()
    f1 = client.get_run(candidat["run_id"]).data.metrics["f1"]
    if f1 < config["qualite"]["f1_min"]:
        raise ValueError("Le meilleur AutoML est sous le seuil d'enregistrement.")
    nom = config["automl"]["modele_registre"]
    version = mlflow.register_model(candidat["modele_uri"], nom).version
    client.set_model_version_tag(nom, version, "version_donnees", candidat["version_donnees"])
    client.set_registered_model_alias(nom, "production", version)
    alias = client.get_model_version_by_alias(nom, "production")
    return {**candidat, "modele_registre": nom, "version": alias.version,
            "alias": "production", "uri": f"models:/{nom}@production"}


def latence(config):
    ports = {
        "reference": config["suivi"]["port_service"],
        "automl": config["automl"]["port_service"],
    }
    nb = config["automl"]["requetes_latence"]
    _, entrees = selection_personnelle(config, config["automl"]["version_donnees"])
    charge = json.dumps({"dataframe_records": entrees.to_dict(orient="records")}).encode()

    def appel(port):
        requete = Request(f"http://127.0.0.1:{port}/invocations", data=charge,
                          headers={"Content-Type": "application/json"}, method="POST")
        depart = time.perf_counter()
        with urlopen(requete, timeout=20) as reponse:
            sortie = json.load(reponse)
            return (time.perf_counter() - depart) * 1000, sortie

    echauffement = {nom: appel(port)[1] for nom, port in ports.items()}
    mesures = {nom: [] for nom in ports}
    for _ in range(nb):
        for nom, port in ports.items():
            mesures[nom].append(appel(port)[0])
    return {"requetes_par_service": nb, "ports": ports, "reponses_echauffement": echauffement,
            "mediane_ms": {nom: statistics.median(vals) for nom, vals in mesures.items()},
            "mesures_ms": mesures}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    sous = cli.add_subparsers(dest="action", required=True)
    registre = sous.add_parser("enregistrer")
    registre.add_argument("sortie", type=Path)
    registre.add_argument("rapports", nargs="+", type=Path)
    mesure = sous.add_parser("mesurer")
    mesure.add_argument("sortie", type=Path)
    args = cli.parse_args()
    config = charger_configuration()
    mlflow.set_tracking_uri(config["suivi"]["uri"])
    resultat = enregistrer(config, args.rapports) if args.action == "enregistrer" else latence(config)
    args.sortie.write_text(json.dumps(resultat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print({k: v for k, v in resultat.items() if k != "mesures_ms"})


if __name__ == "__main__":
    main()
