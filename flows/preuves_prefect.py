"""Exporte les etats, le graphe et la planification via l'API Prefect."""

import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from prefect import get_client
from prefect.client.schemas.filters import (
    FlowRunFilter, FlowRunFilterDeploymentId, LogFilter, LogFilterFlowRunId,
    TaskRunFilter, TaskRunFilterFlowRunId,
)
from prefect.client.schemas.sorting import FlowRunSort
from prefect.schedules import Cron

from reentrainement import charger_configuration, reentrainement


def preuve_execution(source):
    execution = json.loads(source.read_text(encoding="utf-8"))
    id_run = UUID(execution["flow_run_id"])
    uri = charger_configuration()["orchestration"]["prefect_api"]
    response = httpx.get(f"{uri}/flow_runs/{id_run}/graph-v2", timeout=15)
    response.raise_for_status()
    with get_client(sync_client=True) as client:
        taches = client.read_task_runs(task_run_filter=TaskRunFilter(flow_run_id=TaskRunFilterFlowRunId(any_=[id_run])))
        logs = client.read_logs(log_filter=LogFilter(flow_run_id=LogFilterFlowRunId(any_=[id_run])))
    return {
        **execution, "graphe_prefect": response.json(),
        "taches": [{"nom": t.name, "etat": t.state.name, "message": t.state.message,
                    "tentatives": t.run_count} for t in taches],
        "logs": [{"niveau": ligne.level, "message": ligne.message} for ligne in logs],
    }


def planifier(servir):
    config = charger_configuration()
    reg = config["orchestration"]
    schedule = Cron(reg["cron"], timezone=reg["fuseau"])
    nom = reg["deploiement"]
    if servir:
        reentrainement.serve(name=nom, schedules=[schedule], pause_on_shutdown=False,
                             tags=[config["suivi"]["experience"]])
        return
    deployment = reentrainement.to_deployment(
        name=nom, schedules=[schedule], tags=[config["suivi"]["experience"]]
    )
    id_dep = deployment.apply()
    debut = datetime.now(timezone.utc)
    response = httpx.post(
        f"{reg['prefect_api']}/deployments/{id_dep}/schedule",
        json={"start_time": debut.isoformat(), "end_time": (debut + timedelta(days=40)).isoformat(),
              "min_runs": 1, "max_runs": 1},
        timeout=15,
    )
    response.raise_for_status()
    with get_client(sync_client=True) as client:
        result = client.read_deployment(id_dep)
        prochains = []
        for _ in range(20):
            prochains = client.read_flow_runs(
                flow_run_filter=FlowRunFilter(deployment_id=FlowRunFilterDeploymentId(any_=[id_dep])),
                sort=FlowRunSort.EXPECTED_START_TIME_ASC, limit=10,
            )
            prochains = [r for r in prochains if r.state.is_scheduled()]
            if prochains:
                break
            time.sleep(2)
    if not prochains:
        raise RuntimeError("Le planificateur Prefect n'a pas encore cree de run.")
    return {
        "deployment_id": str(id_dep), "nom": result.name,
        "schedules": [s.model_dump(mode="json") for s in result.schedules],
        "prochaine_execution": prochains[0].expected_start_time.astimezone(ZoneInfo(reg["fuseau"])).isoformat(),
        "prochain_run_id": str(prochains[0].id), "prochain_etat": prochains[0].state.name,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("sortie", nargs="?", type=Path)
    cli.add_argument("--execution", type=Path)
    cli.add_argument("--servir", action="store_true")
    args = cli.parse_args()
    if args.servir:
        planifier(True)
        return
    if args.sortie is None:
        cli.error("une sortie est requise")
    resultat = preuve_execution(args.execution) if args.execution else planifier(False)
    args.sortie.write_text(json.dumps(resultat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print({k: v for k, v in resultat.items() if k not in ("logs", "graphe_prefect")})


if __name__ == "__main__":
    main()
