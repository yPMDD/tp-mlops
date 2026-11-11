"""Produit les jeux d'entrainement et de test pour DVC."""

from pathlib import Path

from configuration import charger_configuration
from preparer import lire_classeur, preparer, separer


def main():
    config = charger_configuration()
    donnees = config["donnees"]
    preparees = preparer(lire_classeur(Path(donnees["source"])))
    train, test = separer(preparees, donnees["graine"], donnees["part_test"])
    for nom, jeu in (("train", train), ("test", test)):
        chemin = Path(config["sorties"][nom])
        chemin.parent.mkdir(parents=True, exist_ok=True)
        jeu.to_csv(chemin, index=False)
    print(f"{donnees['version']} : {len(train)} lignes train, {len(test)} lignes test.")


if __name__ == "__main__":
    main()
