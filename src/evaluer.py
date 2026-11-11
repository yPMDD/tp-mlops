"""Mesure les performances de la classe non remboursee."""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

from configuration import charger_configuration
from preparer import CIBLE, VARIABLES


def mesurer(modele, test: pd.DataFrame) -> dict[str, float]:
    reel = test[CIBLE]
    predit = modele.predict(test[list(VARIABLES)])
    return {
        "f1": float(f1_score(reel, predit, pos_label=1, zero_division=0)),
        "precision": float(precision_score(reel, predit, pos_label=1, zero_division=0)),
        "rappel": float(recall_score(reel, predit, pos_label=1, zero_division=0)),
    }


def main():
    config = charger_configuration()
    sorties = config["sorties"]
    metriques = mesurer(joblib.load(sorties["modele"]), pd.read_csv(sorties["test"]))
    chemin = Path(sorties["metriques"])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(metriques, indent=2) + "\n", encoding="utf-8")
    seuil = config["qualite"]["f1_min"]
    statut = "admissible" if metriques["f1"] >= seuil else "non admissible"
    print(f"Classe 1 : {metriques}")
    print(f"Registre : modele {statut} (seuil lu dans params.yaml : {seuil}).")


if __name__ == "__main__":
    main()
