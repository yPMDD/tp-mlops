"""Retrouve le medicament personnel et construit ses entrees."""

from pathlib import Path

from preparer import CIBLE, VARIABLES, lire_classeur, preparer


def selection_personnelle(config: dict, version_donnees: str):
    sources = config["suivi"]["sources"]
    origine = lire_classeur(Path(sources["v1"]))
    preparees = preparer(origine)
    candidats = origine.loc[preparees[CIBLE].eq(1)]
    rang = config["donnees"]["graine"] % len(candidats)
    ligne = candidats.iloc[[rang]]
    code = ligne["CODE"].iloc[0]
    if version_donnees == "v1":
        entrees = preparees.loc[ligne.index, list(VARIABLES)]
    else:
        reference = lire_classeur(Path(sources[version_donnees]))
        dans_reference = reference["CODE"].eq(code)
        if dans_reference.any():
            entrees = preparer(reference).loc[dans_reference, list(VARIABLES)]
        else:
            entrees = preparer(ligne)[list(VARIABLES)].copy()
            entrees["nb_meme_dci"] = int(reference["DCI1"].eq(ligne["DCI1"].iloc[0]).sum())
    return {"rang": rang, "nom": ligne["NOM"].iloc[0], "CODE": code}, entrees
