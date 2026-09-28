"""Etape 6 : recharger le modele par son alias.

C'est le geste que fera le service d'inference du TP 10 : il ne connait ni le
chemin du fichier .pkl, ni le numero de version. Il demande simplement
'models:/fraude-tp1@production' et MLflow resout l'alias vers la bonne version,
meme apres une nouvelle promotion.
"""
import mlflow, pandas as pd

mlflow.set_tracking_uri('http://127.0.0.1:5000')

# Chargement par ALIAS, pas par numero de version
m = mlflow.pyfunc.load_model('models:/fraude-tp1@production')

# Quelle version l'alias a-t-il resolu ?
version = mlflow.MlflowClient().get_model_version_by_alias('fraude-tp1', 'production').version
print(f"alias 'production' -> version {version}")

# Transaction suspecte : gros montant, client recent, 9 paiements en 24 h, de nuit.
# 'montant' est un double dans la signature du modele : le litteral 8500 serait
# un int64 et MLflow 3 refuse de le convertir en float64 sans certitude.
X = pd.DataFrame([{'montant': 8500.0, 'anciennete': 3, 'freq_24h': 9, 'nuit': 1}])
print('prediction:', m.predict(X))  # 1 = transaction suspecte
