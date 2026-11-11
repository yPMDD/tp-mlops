"""Entraine la foret de reference."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from configuration import charger_configuration
from preparer import CIBLE, VARIABLES


def entrainer_foret(train: pd.DataFrame, config: dict, variables=VARIABLES) -> RandomForestClassifier:
    foret = config["foret"]
    modele = RandomForestClassifier(
        n_estimators=foret["arbres"],
        max_depth=foret["profondeur"],
        random_state=config["donnees"]["graine"],
    )
    return modele.fit(train[list(variables)], train[CIBLE])


def main():
    config = charger_configuration()
    modele = entrainer_foret(pd.read_csv(config["sorties"]["train"]), config)
    chemin = Path(config["sorties"]["modele"])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modele, chemin)
    print(f"Foret entrainee : {modele.n_estimators} arbres, profondeur {modele.max_depth}.")


if __name__ == "__main__":
    main()
