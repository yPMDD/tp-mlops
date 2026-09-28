"""Etape 5 : enregistrer la meilleure execution dans le registre MLflow.

Le guide demande de copier le Run ID a la main depuis l'interface. On le fait
automatiquement : on interroge le serveur, on retient l'execution qui maximise
la metrique f1_test, puis on enregistre son modele et on pose l'alias
'production'.

Note MLflow 3 : autolog() ecrit desormais le modele dans un 'LoggedModel'
(mlartifacts/<exp>/models/m-<id>/) et non plus dans le dossier du run. L'URI
'runs://<run_id>/model' du guide ne resout donc plus ; on passe par
search_logged_models() pour retrouver l'ID du modele a partir du run.
"""
import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri('http://127.0.0.1:5000')
client = MlflowClient()
MODEL_NAME = 'fraude-tp1'
exp_id = client.get_experiment_by_name('tp1-decouverte').experiment_id

# 1. Retrouver la meilleure execution sur la metrique de comparaison
runs = client.search_runs(
    experiment_ids=[exp_id],
    filter_string="attributes.status = 'FINISHED'",
    order_by=['metrics.f1_test DESC'],
)
best = runs[0]
run_id = best.info.run_id
print(f"meilleure execution : {best.data.tags['mlflow.runName']}"
      f"  f1_test = {best.data.metrics['f1_test']:.4f}")
print(f"Run ID : {run_id}")

# 2. Retrouver le modele produit par cette execution.
# search_logged_models n'accepte pas de filtre 'runs.source_run_id' : on
# parcourt les modeles de l'experimentation et on garde celui qui pointe
# vers notre Run ID.
logged = [m for m in client.search_logged_models([exp_id])
          if m.source_run_id == run_id]
if not logged:
    raise SystemExit("Aucun modele journalise pour ce run : l'etape 3 a-t-elle ete lancee ?")
print(f"LoggedModel : {logged[0].model_id}")

# 3. Enregistrer dans le registre et promouvoir en production
mv = mlflow.register_model(f'models:/{logged[0].model_id}', MODEL_NAME)
client.set_registered_model_alias(MODEL_NAME, 'production', mv.version)
print(f'version {mv.version} promue en production')
