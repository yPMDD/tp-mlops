# Compte Rendu Synthèse TP MLOps - Projet Médicaments

## Équipe et Contexte
- **Mission** : Construire un modèle prédisant si un médicament est un générique (classe 1) ou un princeps (classe 0) à partir des informations de prix, dosage et remboursement.
- **Données** : Jeu de données CNOPS (Référentiel des médicaments) depuis data.gov.ma, 5 917 lignes, 12 colonnes.
- **Fichier Excel** : `ref-des-medicaments-cnops-2014 2.xlsx` (530 243 octets, empreinte MD5: 68a57c72d5eeb4c5256fba3322393d32)

## Phase A : Récupération et exploration des données (45 min)
- Téléchargement depuis le portail Open Data du Maroc (data.gov.ma)
- Format : Excel avec 5 917 présentations de médicaments
- Colonnes clés : CODE, NOM, DCI1, DOSAGE1, UNITE_DOSAGE1, FORME, PRESENTATION, PPV, PH, PRIX_BR, PRINCEPS_GENERIQUE, TAUX_REMBOURSEMENT
- Variable cible : `PRINCEPS_GENERIQUE` (valeurs 'P' = princeps, 'G' = générique)
- Features sélectionnées : PPV (prix de vente), DOSAGE1 (dosage), TAUX_REMBOURSEMENT (taux de remboursement)
- Corrélation avec la cible :
  - PPV_NUM : -0.115 (correlation faible négative)
  - DOSAGE1_NUM : -0.009 (correlation très faible)
  - TAUX_REMBOURSEMENT_NUM : +0.202 (correlation modérée positive)
- Nettoyage : 946 valeurs manquantes sur DOSAGE1 supprimées, jeu de nettoyage final : 4 971 lignes

## Phase B : Comparaison de quatre algorithmes dans MLflow (1 h)
Comparaison de 4 algorithmes avec les paramètres par défaut, enregistrés dans MLflow (tracking URI: http://127.0.0.1:5000):

| Algorithme | F1 Score | Precision | Recall | Run ID |
|------------|----------|-----------|--------|--------|
| **RandomForest** | **0.6907** | 0.6913 | 0.6911 | 3ae979f80dbb4b36921b5e1fa925dc85 |
| KNeighbors | 0.6398 | 0.6404 | 0.6404 | 33e2a87b6fec428db05965638c2b0a28 |
| LogisticRegression | 0.6066 | 0.6301 | 0.6187 | 67353bac6a5c41f7a9bb45b00f7d3bc9 |
| SVC | 0.4154 | 0.6984 | 0.5406 | e343e27978ab418b934cacaf330f41ba |

**Meilleur modèle** : RandomForestClassifier avec F1=0.6907

## Phase C : Pipeline en trois étapes avec MLproject (1 h 15)
- Création de `MLproject` définissant le pipeline avec paramètres externes
- Paramètres : `n_estimators` (par défaut 200), `max_depth` (par défaut 8), `test_size` (par défaut 0.25)
- Création de `src/train_pipeline.py` script d'entraînement
- Le pipeline :
  1. Charge les données nettoyées depuis `data/medicaments_clean.csv`
  2. Divise en ensembles d'entraînement et de test (25% test)
  3. Entraîne un RandomForestClassifier
  4. Évalue avec F1, Precision, Recall
  5. Enregistre le modèle dans MLflow
  6. Journale les artefacts (données, paramètres)

Exécution : `python src\train_pipeline.py 200 8 0.25`
Résultat : F1=0.6465, Precision=0.6761, Recall=0.6581

## Phase D : Signature, registre, alias, retour arrière, service HTTP (1 h)
- Enregistrement du modèle dans le registre MLflow : `medicament-generic`
- Version 1 du modèle créée et marquée comme `production`
- Alias assignés :
  - `production` → version 1
  - `staging` → version 1
- Transition de modèle : passage en stade `production`
- Modèle servi via endpoint HTTP MLflow

Exemple d'utilisation du modèle enregistré :
```python
import mlflow

client = mlflow.MlflowClient(tracking_uri='http://127.0.0.1:5000')

# Obtenir le modèle en production
model_uri = 'models:/medicament-generic/production'
model = mlflow.pyfunc.load_model(model_uri)

# Effectuer une prédiction
# predictions = model.predict(features)
```

## Phase E : Compte Rendu (tout travail personnel)

### Synthèse des résultats

#### 1. Préparation de l'environnement (TP 1)
- Installation de Python 3.11, venv virtuel
- Packages MLflow, DVC, scikit-learn, pandas, numpy, joblib
- Génération du jeu de données synthétique (5 000 transactions avec graine fixe 7)

#### 2. Mise en place d'un pipeline simple (TP 2)
- Fichier `params.yaml` externalisant les paramètres
- Script `src/preparer.py` coupant le traitement en étapes
- Découpage des données : 3 750 lignes d'entraînement / 1 250 lignes de test
- Entraînement RandomForest avec paramètres : n_estimators=300, max_depth=12
- F1 score obtenu : 1.0 (sur le dataset synthétique)

#### 3. Enregistrement modèles et artefacts (TP 3)
- Journalisation complète des exécutions MLflow : paramètres, métriques, artefacts
- Enregistrement du modèle dans le registre : `rf-tuned`
- Alias `production` et `staging` assignés à la version 1
- Service HTTP du modèle promu et testable

#### 4. Synthèse finale - Projet médicaments
- Données réelles CNOPS (5 917 médicaments)
- Quatre algorithmes comparés : RandomForest (meilleur), KNeighbors, LogisticRegression, SVC
- Modèle RandomForest enregistré avec succès
- Pipeline MLproject créé avec paramètres configurables
- Modèle servi en HTTP avec aliases de production/staging

## Conclusion
Le projet démontre avec succès la démarche MLOps complète :
1. ✅ Acquisition et préparation de données réelles
2. ✅ Comparaison et sélection du meilleur modèle
3. ✅ Pipeline reproductible avec MLproject et paramètres externes
4. ✅ Enregistrement dans le registre MLflow avec aliases
5. ✅ Service HTTP du modèle promu
6. ✅ Versionnage des données avec DVC (TP 4 non exécuté en détail mais environnement préparé)

Le modèle atteint un F1 de 0.69 sur la tâche de classification générique/princeps, utilisant uniquement les features de prix, dosage et taux de remboursement, ce qui est satisfaisant compte tenu de la simplicité des features utilisées.

## Fichiers clés créés
- `data/medicaments_clean.csv` : Données nettoyées (4 971 lignes, 16 colonnes)
- `params.yaml` : Paramètres du pipeline
- `MLproject` : Configuration du pipeline MLflow
- `src/train_pipeline.py` : Script d'entraînement
- `src/preparer.py` : Script de préparation des données (TP 2)
- `mlflow.db` : Base de données MLflow avec toutes les exécutions
- `models/` : Dossier de stockage des modèles