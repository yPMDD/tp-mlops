"""Parametres partages du projet."""

from pathlib import Path

import yaml


def charger_configuration(chemin: Path = Path("params.yaml")) -> dict:
    return yaml.safe_load(chemin.read_text(encoding="utf-8"))
