"""Genere les deux flux Node-RED du TP7 (format runtime, encodage UTF-8).

Ecrit :
  1. C:/Users/S44D/.node-red/flows_DESKTOP-HFB7VAR.json  (charge au demarrage de node-red)
  2. tp-mlops/nodered/flows.json                        (livrable, versionne dans Git)
"""
import json
import pathlib

FLOW1 = "tab_resentrainement"
FLOW2 = "tab_surveiller"
DEPLOY_ID = "97155a66-31ae-4594-b53a-eb75b23446a9"

flows = [
    # ---------- onglet 1 : reentrainement d'un clic ----------
    {"id": FLOW1, "type": "tab", "label": "Réentraîner d'un clic", "disabled": False, "info": ""},
    {
        "id": "inj_retrain", "type": "inject", "z": FLOW1,
        "name": "Lancer le réentraînement",
        "repeat": "", "crontab": "", "once": False, "onceDelay": 0.1, "topic": "",
        "payload": "{}", "payloadType": "json",
        "x": 150, "y": 120, "wires": [["http_prefect"]],
    },
    {
        "id": "http_prefect", "type": "http request", "z": FLOW1,
        "name": "Prefect : créer une exécution",
        "method": "POST", "ret": "obj", "paytoqs": "ignore",
        "url": f"http://127.0.0.1:4200/api/deployments/{DEPLOY_ID}/create_flow_run",
        "persist": False, "proxy": "", "insecureHTTPParser": False, "authType": "",
        "senderr": False, "headers": [],
        "x": 420, "y": 120, "wires": [["chng_resume"]],
    },
    {
        "id": "chng_resume", "type": "change", "z": FLOW1, "name": "Résumé",
        "rules": [{"t": "set", "p": "payload", "pt": "msg",
                   "to": "'Exécution ' & payload.name & ' créée, état : ' & payload.state.name",
                   "tot": "jsonata"}],
        "action": "", "property": "", "from": "", "to": "", "reg": False,
        "x": 650, "y": 120, "wires": [["dbg_reponse"]],
    },
    {
        "id": "dbg_reponse", "type": "debug", "z": FLOW1, "name": "Réponse de Prefect",
        "active": True, "tosidebar": True, "console": False, "tostatus": True,
        "complete": "payload", "targetType": "msg",
        "statusVal": "payload", "statusType": "auto",
        "x": 870, "y": 120, "wires": [],
    },
    # ---------- onglet 2 : surveillance du modele en service ----------
    {"id": FLOW2, "type": "tab", "label": "Surveiller le modèle", "disabled": False, "info": ""},
    {
        "id": "inj_sonde", "type": "inject", "z": FLOW2, "name": "Toutes les 10 s",
        "repeat": "10", "crontab": "", "once": False, "onceDelay": 0.1, "topic": "",
        "payload": '{"dataframe_records":[{"montant":8500.0,"anciennete":3,"freq_24h":9,"nuit":1}]}',
        "payloadType": "json",
        "x": 140, "y": 140, "wires": [["http_modele"]],
    },
    {
        "id": "http_modele", "type": "http request", "z": FLOW2,
        "name": "Modèle : /invocations",
        "method": "POST", "ret": "obj", "paytoqs": "ignore",
        "url": "http://127.0.0.1:8101/invocations",
        "persist": False, "proxy": "", "insecureHTTPParser": False, "authType": "",
        "senderr": False, "headers": [],
        "x": 380, "y": 140, "wires": [["sw_fraude"]],
    },
    {
        "id": "sw_fraude", "type": "switch", "z": FLOW2, "name": "Fraude prédite ?",
        "property": "payload.predictions[0]", "propertyType": "msg",
        "rules": [{"t": "eq", "v": "1", "vt": "num"}, {"t": "eq", "v": "0", "vt": "num"}],
        "checkall": "true", "repair": False, "outputs": 2,
        "x": 600, "y": 140, "wires": [["chng_alerte"], ["dbg_normale"]],
    },
    {
        "id": "chng_alerte", "type": "change", "z": FLOW2, "name": "Message d'alerte",
        "rules": [{"t": "set", "p": "payload", "pt": "msg",
                   "to": "'Transaction suspecte : 8500 MAD la nuit'", "tot": "jsonata"}],
        "action": "", "property": "", "from": "", "to": "", "reg": False,
        "x": 800, "y": 100, "wires": [["dbg_fraude"]],
    },
    {
        "id": "dbg_fraude", "type": "debug", "z": FLOW2, "name": "Alerte fraude",
        "active": True, "tosidebar": True, "console": False, "tostatus": False,
        "complete": "payload", "targetType": "msg", "statusVal": "", "statusType": "auto",
        "x": 1010, "y": 100, "wires": [],
    },
    {
        "id": "dbg_normale", "type": "debug", "z": FLOW2, "name": "Transaction normale",
        "active": True, "tosidebar": True, "console": False, "tostatus": False,
        "complete": "payload", "targetType": "msg", "statusVal": "", "statusType": "auto",
        "x": 1010, "y": 180, "wires": [],
    },
    {
        "id": "catch_http", "type": "catch", "z": FLOW2, "name": "Erreur d'appel",
        "scope": ["http_modele"], "uncaught": False,
        "x": 400, "y": 280, "wires": [["chng_incident"]],
    },
    {
        "id": "chng_incident", "type": "change", "z": FLOW2, "name": "Horodater l'incident",
        "rules": [{"t": "set", "p": "payload", "pt": "msg",
                   "to": "$now() & ' ALERTE service du modele indisponible : ' & error.message",
                   "tot": "jsonata"}],
        "action": "", "property": "", "from": "", "to": "", "reg": False,
        "x": 630, "y": 280, "wires": [["dbg_service"], ["fichier_alertes"]],
    },
    {
        "id": "dbg_service", "type": "debug", "z": FLOW2, "name": "Alerte service",
        "active": True, "tosidebar": True, "console": False, "tostatus": False,
        "complete": "payload", "targetType": "msg", "statusVal": "", "statusType": "auto",
        "x": 860, "y": 240, "wires": [],
    },
    {
        "id": "fichier_alertes", "type": "file", "z": FLOW2, "name": "alertes.log",
        "filename": "C:\\Users\\S44D\\Documents\\5iir\\MLOps\\tp-mlops\\reports\\alertes.log",
        "filenameType": "str", "appendNewline": True, "createDir": True,
        "overwriteFile": "false", "encoding": "none",
        "x": 860, "y": 320, "wires": [],
    },
]

pathlib.Path("nodered").mkdir(exist_ok=True)
for target in (r"C:\Users\S44D\.node-red\flows_DESKTOP-HFB7VAR.json", "nodered/flows.json"):
    p = pathlib.Path(target)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(flows, indent=4, ensure_ascii=False), encoding="utf-8")
    print("ecrit :", p)
