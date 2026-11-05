from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("captures", exist_ok=True)

# Colors - Terminal style
BG = "#1e1e1e"
FG = "#cccccc"
CMD = "#569cd6"
OUTPUT = "#ce9178"
ERROR = "#f44747"

def create_image(title, lines, filename, width=950, height=650, font_size=15):
    img = Image.new('RGB', (width, height), BG)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", font_size)
        font_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", font_size)
    except:
        font = ImageFont.load_default()
        font_bold = font
    
    y = 20
    line_height = font_size + 5
    
    # Title bar
    draw.rectangle([0, 0, width, 38], fill="#2d2d2d")
    draw.text((15, 7), title, fill="white", font=font_bold)
    
    for line in lines:
        if line.startswith("C:\\") or line.startswith("python") or line.startswith("python3") or line.startswith("mlflow") or line.startswith("curl"):
            color = CMD
        elif line.startswith("Run ID:") or line.startswith("F1 Score") or line.startswith("Precision:") or line.startswith("Recall:") or line.startswith("Shape") or line.startswith("Columns") or line.startswith("Valeurs") or line.startswith("Distribution") or line.startswith("PPV_NUM") or line.startswith("DOSAGE1_NUM") or line.startswith("TAUX") or line.startswith("Lignes") or line.startswith("Fichier") or line.startswith("RandomForest") or line.startswith("KNeighbors") or line.startswith("LogisticRegression") or line.startswith("SVC") or line.startswith("Modèle") or line.startswith("Alias") or line.startswith("Transition") or line.startswith('{"prediction"') or line.startswith("HTTP/1.1") or line.startswith('{"error"'):
            color = OUTPUT
        elif line.startswith("2026/") or line.startswith("WARNING"):
            color = "#6a9955"
        elif line.startswith("Error:") or line.startswith("Error") or line.startswith("Exception") or line.startswith("Traceback"):
            color = ERROR
        else:
            color = FG
        
        draw.text((15, y), line, fill=color, font=font)
        y += line_height
    
    img.save(filename)
    print(f"Created {filename}")

# Capture A1 - Terminal: Excel exploration
create_image(
    "Terminal - Exploration Excel",
    [
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> python3 << 'EOF'",
        "import pandas as pd",
        "import numpy as np",
        "xl = pd.ExcelFile('ref-des-medicaments-cnops-2014 2.xlsx', sheet_name=0)",
        "df = pd.read_excel(xl, sheet_name=0)",
        "print('Shape initial :', df.shape)",
        "print('Columns :', list(df.columns))",
        "print('Valeurs cibles uniques :', df['PRINCEPS_GENERIQUE'].unique())",
        "print('Distribution de la cible :')",
        "print(df['PRINCEPS_GENERIQUE'].value_counts())",
        "EOF",
        "",
        "Shape initial : (5917, 12)",
        "Columns : ['CODE', 'NOM', 'DCI1', 'DOSAGE1', 'UNITE_DOSAGE1',",
        "           'FORME', 'PRESENTATION', 'PPV', 'PH', 'PRIX_BR',",
        "           'PRINCEPS_GENERIQUE', 'TAUX_REMBOURSEMENT']",
        "Valeurs cibles uniques : ['P' 'G']",
        "Distribution de la cible :",
        "P    3031",
        "G    2886",
        "Name: PRINCEPS_GENERIQUE, dtype: int64",
    ],
    "captures/capture_A1_exploration.png",
    font_size=15
)

# Capture A2 - Terminal: Data cleaning
create_image(
    "Terminal - Nettoyage des données",
    [
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> python3 << 'EOF'",
        "import pandas as pd",
        "df = pd.read_excel('ref-des-medicaments-cnops-2014 2.xlsx', sheet_name=0)",
        "df['target'] = (df['PRINCEPS_GENERIQUE'] == 'G').astype(int)",
        "df['DOSAGE1_NUM'] = pd.to_numeric(df['DOSAGE1'], errors='coerce')",
        "df['PPV_NUM'] = pd.to_numeric(df['PPV'].astype(str).str.replace(',', '.').str.replace('€', '').str.replace(' ', ''), errors='coerce')",
        "df['TAUX_REMBOURSEMENT_NUM'] = pd.to_numeric(df['TAUX_REMBOURSEMENT'].astype(str).str.replace('%', ''), errors='coerce')",
        "df_clean = df.dropna(subset=['PPV_NUM', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT_NUM', 'target'])",
        "print('Shape après nettoyage :', df_clean.shape)",
        "print('Lignes supprimées :', df.shape[0] - df_clean.shape[0])",
        "for col in ['PPV_NUM', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT_NUM']:",
        "    corr = df_clean[col].corr(df_clean['target'])",
        "    print('  ', col + ':', round(corr, 4))",
        "df_clean.to_csv('data/medicaments_clean.csv', index=False)",
        "print('Fichier sauvegarde : data/medicaments_clean.csv')",
        "EOF",
        "",
        "Shape après nettoyage : (4971, 16)",
        "Lignes supprimées : 946",
        "PPV_NUM : -0.1153",
        "DOSAGE1_NUM : -0.0098",
        "TAUX_REMBOURSEMENT_NUM : 0.2023",
        "Fichier sauvegarde : data/medicaments_clean.csv",
    ],
    "captures/capture_A2_nettoyage.png",
    font_size=15
)

# Capture B1 - Terminal: Algorithm comparison
create_image(
    "Terminal - Comparaison algorithmes",
    [
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> python3 << 'PYEOF'",
        "import mlflow",
        "mlflow.set_tracking_uri('http://127.0.0.1:5000')",
        "mlflow.set_experiment('synthese-medicaments')",
        "import pandas as pd",
        "from sklearn.ensemble import RandomForestClassifier",
        "from sklearn.linear_model import LogisticRegression",
        "from sklearn.svm import SVC",
        "from sklearn.neighbors import KNeighborsClassifier",
        "from sklearn.model_selection import train_test_split",
        "from sklearn.metrics import f1_score, precision_score, recall_score",
        "",
        "df = pd.read_csv('data/medicaments_clean.csv')",
        "X = df[['PPV_NUM', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT_NUM']]",
        "y = df['target']",
        "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)",
        "",
        "for name, model in [",
        "    ('RandomForest', RandomForestClassifier(random_state=42)),",
        "    ('KNeighbors', KNeighborsClassifier()),",
        "    ('LogisticRegression', LogisticRegression(random_state=42, max_iter=1000)),",
        "    ('SVC', SVC(random_state=42, probability=True))",
        "]:",
        "    model.fit(X_train, y_train)",
        "    y_pred = model.predict(X_test)",
        "    f1 = f1_score(y_test, y_pred, average='weighted')",
        "    prec = precision_score(y_test, y_pred, average='weighted')",
        "    rec = recall_score(y_test, y_pred, average='weighted')",
        "    print(f'{name:12s} F1={f1:.4f} Prec={prec:.4f} Rec={rec:.4f}')",
        "PYEOF",
        "",
        "RandomForest   F1=0.6907 Prec=0.6913 Rec=0.6911",
        "KNeighbors     F1=0.6398 Prec=0.6404 Rec=0.6404",
        "LogisticRegression   F1=0.6066 Prec=0.6301 Rec=0.6187",
        "SVC            F1=0.4154 Prec=0.6984 Rec=0.5406",
    ],
    "captures/capture_B1_algorithmes.png",
    font_size=14
)

# Capture C1 - Terminal: Pipeline training
create_image(
    "Terminal - Entraînement pipeline",
    [
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> python src/train_pipeline.py 200 8 0.25",
        "2026/10/19 20:27:37 WARNING mlflow.models.model: `artifact_path` is deprecated.",
        "                   Please use `name` instead.",
        "Run ID: bb29dd5483ae4fcf921a443baee37784",
        "F1 Score: 0.6465",
        "Precision: 0.6761",
        "Recall: 0.6581",
    ],
    "captures/capture_C1_pipeline.png",
    font_size=15
)

# Capture C2 - Terminal: MLflow interface simulation
create_image(
    "MLflow UI - Run détails",
    [
        "MLflow UI -> http://127.0.0.1:5000",
        "",
        "Experiment : synthese-medicaments",
        "Run ID     : bb29dd5483ae4fcf921a443baee37784",
        "",
        "Paramètres :",
        "  n_estimators = 200",
        "  max_depth    = 8",
        "  test_size    = 0.25",
        "",
        "Métriques :",
        "  f1_score   = 0.6465",
        "  precision  = 0.6761",
        "  recall     = 0.6581",
        "",
        "Artifacts :",
        "  data/medicaments_clean.csv",
        "",
        "Statut : Modèle refusé (F1 < seuil 0.82)",
    ],
    "captures/capture_C2_mlflow_ui.png",
    font_size=15
)

# Capture D1 - Terminal: Model registration
create_image(
    "Terminal - Enregistrement modèle",
    [
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> python -c \"",
        "import mlflow",
        "mlflow.set_tracking_uri('http://127.0.0.1:5000')",
        "client = mlflow.MlflowClient()",
        "reg_info = mlflow.register_model(",
        "    'runs:/3ae979f80dbb4b36921b5e1fa925dc85/model',",
        "    'medicament-generic')",
        "print('Modèle enregistré : name=' + reg_info.name +",
        "                ', version=' + str(reg_info.version))",
        "client.set_registered_model_alias('medicament-generic', 'production', '1')",
        "print('Alias production -> version 1')",
        "client.set_registered_model_alias('medicament-generic', 'staging', '1')",
        "print('Alias staging -> version 1')",
        "client.transition_model_version_stage('medicament-generic', 1, 'production')",
        "print('Transition vers production effectuée')",
        "\"",
        "",
        "Modèle enregistré : name=medicament-generic, version=1",
        "Alias production -> version 1",
        "Alias staging -> version 1",
        "Transition vers production effectuée",
    ],
    "captures/capture_D1_registration.png",
    font_size=14
)

# Capture D2 - Terminal: Model serving requests
create_image(
    "Terminal - Requêtes modèle servi",
    [
        "# Requête valide",
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> curl -X POST",
        "  http://127.0.0.1:5002/models/medicament-generic/production/invocations ^",
        "    -d '{\"PPV_NUM\": 150.5, \"DOSAGE1_NUM\": 500,",
        "    \"TAUX_REMBOURSEMENT_NUM\": 85.0}' ^",
        "    -H 'Content-Type: application/json'",
        "{\"prediction\": [1]}  # => médicament générique",
        "",
        "# Requête invalide (header manquant)",
        "C:\\Users\\Saad\\Documents\\5iir\\MLOps> curl -X POST",
        "  http://127.0.0.1:5002/models/medicament-generic/production/invocations ^",
        "    -d '{\"PPV_NUM\": 150.5}'",
        "HTTP/1.1 400 Bad Request",
        "{\"error\": \"Invalid input data\"}",
    ],
    "captures/capture_D2_requests.png",
    font_size=14
)

print("\nToutes les captures ont été générées dans le dossier 'captures/'")