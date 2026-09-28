import sys, mlflow, mlflow.sklearn, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

n_estimators = int(sys.argv[1]) if len(sys.argv) > 1 else 300 # 1er argument
max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 12 # 2e argument

mlflow.set_tracking_uri('http://127.0.0.1:5000') # serveur de l'etape 2
mlflow.set_experiment('tp1-decouverte') # regroupe les executions
mlflow.sklearn.autolog() # capture automatique

df = pd.read_csv('data/transactions.csv')
X, y = df.drop(columns='fraude'), df['fraude'] # entrees / cible
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)


with mlflow.start_run(run_name=f'rf-{n_estimators}-{max_depth}'):
    m = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42).fit(Xtr, ytr)
    f1 = f1_score(yte, m.predict(Xte))
    mlflow.log_metric('f1_test', f1) # metrique de comparaison
    print('F1 =', round(f1, 4))
