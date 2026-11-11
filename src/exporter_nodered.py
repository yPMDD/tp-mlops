"""Exporte le flux de surveillance de la classe 1."""

import argparse
import json
from pathlib import Path

from configuration import charger_configuration
from medicament_personnel import selection_personnelle


def main(destination):
    config = charger_configuration()
    suivi = config["suivi"]
    identite, entrees = selection_personnelle(config, "v1")
    corps = json.dumps({"dataframe_records": entrees.to_dict(orient="records")})
    onglet, inject, http, condition, alerte, journal = ("e400", "e401", "e402", "e403", "e404", "e405")
    noeuds = [
        {"id": onglet, "type": "tab", "label": suivi["experience"], "disabled": False},
        {"id": inject, "type": "inject", "z": onglet, "name": "Toutes les minutes",
         "props": [{"p": "payload"}, {"p": "headers", "v": '{"Content-Type":"application/json"}', "vt": "json"}],
         "payload": corps, "payloadType": "json", "repeat": str(config["orchestration"]["periode_nodered"]),
         "crontab": "", "once": True, "onceDelay": 0.5, "x": 150, "y": 100, "wires": [[http]]},
        {"id": http, "type": "http request", "z": onglet, "name": "Service forêt",
         "method": "POST", "ret": "obj", "paytoqs": "ignore",
         "url": f"http://127.0.0.1:{suivi['port_service']}/invocations", "persist": False,
         "authType": "", "headers": [], "x": 350, "y": 100, "wires": [[condition]]},
        {"id": condition, "type": "switch", "z": onglet, "name": "Classe 1 ?",
         "property": "payload.predictions[0]", "propertyType": "msg",
         "rules": [{"t": "eq", "v": "1", "vt": "num"}], "checkall": "true", "repair": False,
         "outputs": 1, "x": 520, "y": 100, "wires": [[alerte]]},
        {"id": alerte, "type": "change", "z": onglet, "name": "Composer alerte",
         "rules": [{"t": "set", "p": "payload", "pt": "msg",
                    "to": f"ALERTE classe 1 : {identite['nom']} ({identite['CODE']})", "tot": "str"}],
         "x": 690, "y": 100, "wires": [[journal]]},
        {"id": journal, "type": "debug", "z": onglet, "name": "Alerte remboursement",
         "active": True, "tosidebar": True, "console": True, "tostatus": False,
         "complete": "payload", "targetType": "msg", "x": 880, "y": 100, "wires": []},
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(noeuds, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("destination", type=Path)
    main(cli.parse_args().destination)
