"""Releve reproductible des mesures A2 a A6."""

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from preparer import CIBLE, VARIABLES, lire_classeur, preparer, separer


def main(chemin: Path, graine: int | None, part_test: float | None):
    brut = lire_classeur(chemin)
    donnees = preparer(brut)
    pos = donnees[CIBLE].eq(1)
    pos_count = int(pos.sum())

    dosage = brut["DOSAGE1"]
    vides = dosage.isna() | dosage.astype(str).str.strip().eq("")
    invalides = pd.to_numeric(dosage, errors="coerce").isna()
    exemples = (brut.loc[invalides & ~vides, ["DOSAGE1", "UNITE_DOSAGE1"]]
                .value_counts().head(3))
    dci = brut["DCI1"].value_counts()

    print("A2  Taille (octets) :", chemin.stat().st_size)
    print("A2  MD5 :", hashlib.md5(chemin.read_bytes()).hexdigest())
    print(f"A3  Lignes : {len(brut)} | Colonnes : {len(brut.columns)}")
    print(f"A3  Non remboursees : {pos_count} ({pos.mean():.2%})")
    print(f"A4  Dosages vides : {vides.sum()} | Non convertibles, vides inclus : {invalides.sum()}")
    for (valeur, unite), count in exemples.items():
        print(f"A4  Exemple : {valeur} ({unite}), {count} lignes")
    print(f"A5  DCI la plus frequente : {dci.index[0]} ({dci.iloc[0]} presentations)")

    if graine is None:
        return
    if pos_count != 1977:
        raise ValueError(f"Le rang personnel suppose 1977 lignes de classe 1, obtenu : {pos_count}")
    train, test = separer(donnees, graine, part_test)
    rang = graine % pos_count
    personnel = brut.loc[pos].iloc[rang]
    print(f"A6  Entrainement : {len(train)} | Test : {len(test)}")
    print(f"A6  Classe 1 dans le test : {test[CIBLE].sum()} ({test[CIBLE].mean():.2%})")
    print("A6  Variables :", ", ".join(VARIABLES))
    print(f"Medicament personnel, rang {rang} : {personnel['NOM']} (CODE {personnel['CODE']})")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("classeur", type=Path)
    cli.add_argument("--graine", type=int)
    cli.add_argument("--part-test", type=float)
    args = cli.parse_args()
    if (args.graine is None) != (args.part_test is None):
        cli.error("--graine et --part-test doivent etre fournis ensemble")
    main(args.classeur, args.graine, args.part_test)
