"""Trace le F1 a partir des quatre executions MLflow de C1."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from configuration import charger_configuration


def main(entree: Path, sortie: Path):
    runs = json.loads(entree.read_text(encoding="utf-8"))
    forets = sorted((r for r in runs if r["algorithme"] == "foret"), key=lambda r: r["profondeur"])
    logistique = next(r for r in runs if r["algorithme"] == "logistique")
    profondeurs = [r["profondeur"] for r in forets]
    scores = [r["f1"] for r in forets]
    fig, ax = plt.subplots(figsize=(7.5, 4.2), layout="constrained")
    ax.plot(profondeurs, scores, marker="o", color="#126c69", label="Forêt aléatoire")
    ax.axhline(logistique["f1"], linestyle="--", color="#b75b25", label="Régression logistique")
    for profondeur, score in zip(profondeurs, scores):
        ax.annotate(f"{score:.4f}", (profondeur, score), xytext=(0, 8), textcoords="offset points", ha="center")
    ax.set_xticks(profondeurs)
    ax.set_xlabel("Profondeur maximale de la forêt")
    ax.set_ylabel("F1 de la classe 1 sur le test")
    ax.set_ylim(0.45, 0.86)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower right")
    ax.set_title(charger_configuration()["suivi"]["experience"] + " | Données V2")
    fig.savefig(sortie, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("entree", type=Path)
    cli.add_argument("sortie", type=Path)
    args = cli.parse_args()
    main(args.entree, args.sortie)
