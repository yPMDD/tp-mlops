"""Construit la v2 sans modifier le classeur source."""

import argparse
from pathlib import Path

from openpyxl import Workbook, load_workbook


def main(source: Path, destination: Path):
    if destination.exists():
        raise FileExistsError(destination)
    with source.open("rb") as fichier:
        brut = load_workbook(fichier, read_only=True, data_only=True)
        lignes = iter(brut.active.values)
        colonnes = next(lignes)
        ppv = colonnes.index("PPV")
        sortie = Workbook(write_only=True)
        feuille = sortie.create_sheet(brut.active.title)
        feuille.append(colonnes)
        gardees = supprimees = 0
        for ligne in lignes:
            if ligne[ppv] == 0:
                supprimees += 1
            else:
                feuille.append(ligne)
                gardees += 1
        brut.close()
    destination.parent.mkdir(parents=True, exist_ok=True)
    sortie.save(destination)
    print(f"v2 : {gardees} lignes conservees, {supprimees} lignes PPV = 0 retirees.")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("destination", type=Path)
    args = cli.parse_args()
    main(args.source, args.destination)
