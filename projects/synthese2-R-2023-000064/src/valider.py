"""Valide le classeur avant le calcul des variables."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from configuration import charger_configuration
from preparer import lire_classeur


COLONNES = (
    "CODE", "NOM", "DCI1", "DOSAGE1", "UNITE_DOSAGE1", "FORME",
    "PRESENTATION", "PPV", "PH", "PRIX_BR", "PRINCEPS_GENERIQUE",
    "TAUX_REMBOURSEMENT",
)


def valider(donnees: pd.DataFrame) -> None:
    manquantes = sorted(set(COLONNES) - set(donnees.columns))
    if manquantes:
        raise ValueError("colonnes manquantes : " + ", ".join(manquantes))
    if donnees.empty:
        raise ValueError("le classeur ne contient aucune presentation")
    for colonne in ("PPV", "PH", "PRIX_BR"):
        prix = pd.to_numeric(donnees[colonne], errors="coerce")
        if not (np.isfinite(prix) & prix.ge(0)).all():
            raise ValueError(f"{colonne} doit contenir des prix finis et positifs ou nuls")
    if not donnees["TAUX_REMBOURSEMENT"].isin(["0%", "70%"]).all():
        raise ValueError("TAUX_REMBOURSEMENT doit valoir 0% ou 70%")
    if not donnees["PRINCEPS_GENERIQUE"].isin(["P", "G"]).all():
        raise ValueError("PRINCEPS_GENERIQUE doit valoir P ou G")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--classeur", type=Path)
    args = cli.parse_args()
    source = args.classeur or Path(charger_configuration()["donnees"]["source"])
    try:
        valider(lire_classeur(source))
    except ValueError as erreur:
        raise SystemExit(f"Validation refusee : {erreur}") from erreur
    print("Validation des donnees brutes : OK.")
