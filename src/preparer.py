"""Preparation commune du referentiel CNOPS."""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


VARIABLES = (
    "ppv", "ph", "prix_br", "ecart_br", "dosage", "generique",
    "nb_meme_dci", "injectable", "comprime",
)
CIBLE = "non_rembourse"


def lire_classeur(chemin: Path) -> pd.DataFrame:
    return pd.read_excel(chemin, dtype={"CODE": str}, keep_default_na=False)


def preparer(donnees: pd.DataFrame) -> pd.DataFrame:
    """Construit les neuf variables dans l'ordre prescrit, puis la cible."""
    ppv = donnees["PPV"].astype("float64")
    prix_br = donnees["PRIX_BR"].astype("float64")
    forme = donnees["FORME"].astype(str)
    return pd.DataFrame({
        "ppv": ppv,
        "ph": donnees["PH"].astype("float64"),
        "prix_br": prix_br,
        "ecart_br": ppv - prix_br,
        "dosage": pd.to_numeric(donnees["DOSAGE1"], errors="coerce").fillna(0.0),
        "generique": donnees["PRINCEPS_GENERIQUE"].eq("G").astype("int64"),
        "nb_meme_dci": donnees.groupby("DCI1")["DCI1"].transform("size"),
        "injectable": forme.str.contains("INJECT", regex=False).astype("int64"),
        "comprime": forme.str.startswith("COMPRIME").astype("int64"),
        CIBLE: donnees["TAUX_REMBOURSEMENT"].eq("0%").astype("int64"),
    }, index=donnees.index)


def separer(donnees: pd.DataFrame, graine: int, part_test: float):
    return train_test_split(
        donnees, test_size=part_test, random_state=graine, stratify=donnees[CIBLE]
    )
