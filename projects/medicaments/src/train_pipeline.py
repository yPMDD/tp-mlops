import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score
import sys

def main(n_estimators=200, max_depth=8, test_size=0.25):
    mlflow.set_tracking_uri('http://127.0.0.1:5000')
    mlflow.set_experiment('synthese-medicaments')
    
    # Load data
    df = pd.read_csv('data/medicaments_clean.csv')
    
    X = df[['PPV_NUM', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT_NUM']]
    y = df['target']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    
    # Train model
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average='weighted')
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    
    # Log to MLflow
    with mlflow.start_run(run_name=f'pipeline-{n_estimators}-{max_depth}') as run:
        mlflow.log_param('n_estimators', n_estimators)
        mlflow.log_param('max_depth', max_depth)
        mlflow.log_param('test_size', test_size)
        mlflow.log_metric('f1_score', f1)
        mlflow.log_metric('precision', precision)
        mlflow.log_metric('recall', recall)
        
        # Log model
        mlflow.sklearn.log_model(model, 'model', skops_trusted_types=['sklearn.tree._tree.Tree'])
        
        # Log artifacts
        mlflow.log_artifact('data/medicaments_clean.csv')
        
        print(f'Run ID: {run.info.run_id}')
        print(f'F1 Score: {f1:.4f}')
        print(f'Precision: {precision:.4f}')
        print(f'Recall: {recall:.4f}')
    
    return f1

if __name__ == '__main__':
    n_estimators = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    test_size = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    
    f1 = main(n_estimators, max_depth, test_size)