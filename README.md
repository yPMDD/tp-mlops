# TP de synthèse 2 — Remboursement

Projet CNOPS pour l'exercice de synthèse des TPs 1 à 8. Le [compte rendu](compte-rendu.pdf) couvre A1 à F13. Les preuves d'exécution, métriques, journaux et graphiques sont dans [reports](reports).

## Rejouer le pipeline

Le ZIP de remise contient le dépôt autonome, avec `.git`, les tags `donnees-v1` et `donnees-v2` et les pointeurs DVC. Extraire ce ZIP pour utiliser les commandes Git et DVC de l'exercice depuis sa racine. Le stockage local `stockage-dvc` doit être accessible comme dossier voisin. Les classeurs et les sorties suivies par DVC se récupèrent via `dvc pull`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
dvc pull
dvc repro
```

Le classeur brut provient du [portail Open Data du Maroc](https://data.gov.ma/data/fr/dataset/referentiel-des-medicaments), licence ODbL. La preuve de provenance figure dans `reports/a2-portail.json`. Pour reconstruire la version dérivée à partir du classeur brut, utiliser `src/creer_v2.py`.

## Suivi, service et orchestration

Le serveur de suivi s'ouvre sur le port 5000 depuis la racine du dépôt.

```powershell
mlflow server --host 127.0.0.1 --port 5000 --workers 1 --backend-store-uri sqlite:///mlflow.db --artifacts-destination ./mlartifacts
```

Dans un second terminal, définir `MLFLOW_TRACKING_URI=http://127.0.0.1:5000`. Les scripts `src/journaliser.py`, `src/registre.py`, `src/comparaison_automl.py` et `src/servir_automl.py` exposent leurs arguments avec `--help`. Les valeurs de l'expérience, du modèle et du seuil figurent dans `params.yaml`. Une fois les alias recréés, servir `models:/remboursement-rf@production` sur 8000 et `models:/remboursement-automl@production` sur 8100 avec `mlflow models serve --env-manager local`.

Pour Prefect, démarrer le serveur local sur 4200, définir `PREFECT_API_URL=http://127.0.0.1:4200/api`, puis exécuter `python flows/preuves_prefect.py --servir` pour maintenir le runner du déploiement mensuel. Le flux Node-RED s'importe depuis `nodered/remboursement.json` et utilise le service sur 8000.

## Orange

Installer `orange/requirements.txt` dans un environnement séparé. Ouvrir `orange/remboursement.ows` après `dvc pull`. Test and Score utilise les données de test séparées. Dans Explain Prediction, sélectionner la classe 1. `orange/verifier_workflow.py` permet de rejouer les widgets et d'exporter leurs résultats.
