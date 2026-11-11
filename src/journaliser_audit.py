"""Ajoute les preuves d'explicabilite au run de production."""

import argparse
import json
from pathlib import Path

import mlflow

from configuration import charger_configuration


def main(sortie):
    suivi = charger_configuration()["suivi"]
    mlflow.set_tracking_uri(suivi["uri"])
    client = mlflow.MlflowClient()
    version = client.get_model_version_by_alias(suivi["modele_rf"], "production")
    if version.tags.get("version_donnees") != "v1":
        raise ValueError("La production doit correspondre aux donnees V1.")
    run_id = version.run_id
    fichiers = (
        "MODEL_CARD.md", "reports/f1-importances.png", "reports/f2-pdp-ice.png",
        "reports/f4-shap.png", "reports/f11-comparaison.png",
    )
    for fichier in fichiers:
        client.log_artifact(run_id, fichier, artifact_path="audit-explicabilite")
    objets = [a.path for a in client.list_artifacts(run_id, "audit-explicabilite")]
    if not {f"audit-explicabilite/{Path(p).name}" for p in fichiers} <= set(objets):
        raise RuntimeError("Artefacts d'audit absents de MLflow.")
    preuve = {"run_production": run_id, "version": version.version, "artefacts": sorted(objets)}
    sortie.write_text(json.dumps(preuve, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(preuve)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("sortie", type=Path)
    main(cli.parse_args().sortie)
