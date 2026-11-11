"""Envoie les deux requetes demandees par C6 au service local."""

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import mlflow

from configuration import charger_configuration
from medicament_personnel import selection_personnelle


def interroger(url: str, ligne: dict) -> dict:
    charge = {"dataframe_records": [ligne]}
    requete = Request(
        url, data=json.dumps(charge).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urlopen(requete, timeout=15) as reponse:
            return {"requete": charge, "code_http": reponse.status, "reponse": json.load(reponse)}
    except HTTPError as erreur:
        with erreur:
            return {"requete": charge, "code_http": erreur.code, "reponse": json.load(erreur)}


def main(sortie: Path):
    config = charger_configuration()
    suivi = config["suivi"]
    mlflow.set_tracking_uri(suivi["uri"])
    production = mlflow.MlflowClient().get_model_version_by_alias(suivi["modele_rf"], "production")
    medicament, entrees = selection_personnelle(config, production.tags["version_donnees"])
    ligne = entrees.to_dict(orient="records")[0]
    sans_dosage = {nom: valeur for nom, valeur in ligne.items() if nom != "dosage"}
    url = f"http://127.0.0.1:{suivi['port_service']}/invocations"
    resultat = {
        "uri": url,
        "production": production.version,
        "medicament": medicament,
        "valide": interroger(url, ligne),
        "sans_dosage": interroger(url, sans_dosage),
    }
    texte = json.dumps(resultat, ensure_ascii=False, indent=2)
    sortie.write_text(texte + "\n", encoding="utf-8")
    print(texte)
    if resultat["valide"]["code_http"] != 200:
        raise SystemExit("Echec de la requete complete")
    manque = resultat["sans_dosage"]
    if manque["code_http"] not in (400, 422) or "dosage" not in str(manque["reponse"]):
        raise SystemExit("La requete sans dosage n'a pas ete rejetee pour la raison attendue")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("sortie", type=Path)
    main(cli.parse_args().sortie)
