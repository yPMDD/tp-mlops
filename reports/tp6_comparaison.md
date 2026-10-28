# TP6 – Comparaison des trois chaînes de modélisation

Toutes les valeurs ci-dessous ont été mesurées sur mon poste, dans `tp-mlops`,
avec le dataset canonique `data/transactions.csv` (5000 lignes, graine 7).

| Critère              | Manuel (TP 3)              | H2O AutoML                                      | FLAML               |
|----------------------|----------------------------|-------------------------------------------------|---------------------|
| F1 sur le jeu test   | 0.8636                     | 0.8623                                          | 0.8359              |
| Modèle retenu        | forêt 300                  | StackedEnsemble_AllModels_1                     | LightGBM (lgbm)     |
| Latence médiane      | – (pas d'endpoint au TP 3) | 52 à 59 ms (runs : 54.9, 53.9, 52.0, puis 59.0) | 6.7 à 6.9 ms        |
| Taille du modèle     | 7.8 Mo (8 145 241 octets)  | 5.4 Mo (5 352 445 octets dans mlartifacts)      | 43 Ko (44 116 o)    |
| Dépendances en prod  | Python (sklearn/joblib)    | Python + Java + serveur H2O maintenu actif      | Python (+ lightgbm) |
| Explicabilité        | importances Gini (sklearn) | importances natives affichées dans H2O Flow     | rien d'affiché par défaut |

## Mes mesures face aux valeurs de préparation du sujet

- **F1 H2O = 0.8623** (projet `AutoML_1_20261028_22856`). Le sujet annonçait
  0.8464 : la machine, la version d'H2O (3.46.0.12) et le pool de modèles
  diffèrent ; sur mon poste XGBoost est absent (event log :
  « AutoML: XGBoost is not available; skipping it. »).
- **F1 FLAML = 0.8359** avec lgbm et 25 essais : identique à la valeur du sujet
  (seed 42, même découpage train/test).
- Taille du modèle H2O : le dossier d'artefacts MLflow pèse
  **5 352 445 octets** (le sujet donnait 4.7 Mo). Le StackedEnsemble embarque
  14 modèles, ce qui reste compact.
- Taille FLAML : `model_flaml.pkl` = **44 116 octets**, comme les 44 Ko du sujet.
- Taille forêt TP 3 : `model.pkl` = **8 145 241 octets**, soit 7.8 Mo,
  identique au sujet.

## Pourquoi la latence H2O est ~8 fois celle de FLAML

Le sujet évoque un facteur 50 ; chez moi la médiane est de **54 ms pour H2O
contre 6.7 ms pour FLAML**, soit un facteur d'environ 8. La raison est
architecturale et ne dépend pas de la machine :

- H2O : le modèle vit dans un **serveur Java séparé**. À chaque appel, le JSON
  est converti en DataFrame pandas, puis uploadé vers `localhost:54321` sous
  forme de `H2OFrame` — les logs du serveur montrent une nouvelle trame
  `Key_Frame__upload_...hex` re-créée à **chaque** requête — puis prédit, et le
  résultat est reconverti en DataFrame puis JSON. Deux sérialisations et un
  aller-retour réseau local par inférence.
- FLAML : le LightGBM est **chargé en mémoire du processus uvicorn**. La
  prédiction est un simple appel numpy, sans re-sérialisation des données.

## Ce que l'étape 7 a révélé

Après un redémarrage de H2O, l'appel du port 8100 échoue en **HTTP 400** :
`H2OKeyNotFoundArgumentException: Object 'StackedEnsemble_..._20261028_22856'
not found`. Conclusion : le registre MLflow ne conserve qu'une **référence**
vers un objet vivant dans la mémoire du serveur H2O, qui doit rester actif.
Après relance du point de terminaison, le modèle se recharge dans le nouveau
serveur et tout refonctionne (même prédiction, p1 = 0.99999, médiane 59 ms).
FLAML sert, lui, depuis un `.pkl` **autonome** : H2O arrêté, le port 8101
répond toujours (médiane 6.9 ms).

## Modèle à déployer en production

La forêt du TP 3 garde le meilleur F1 (0.8636), mais l'écart avec H2O (0.8623)
est négligeable (~0.001). Pour autoriser un **paiement en temps réel**, je
déploierais **FLAML/LightGBM** : environ 8× plus rapide, artefact autonome
(un seul `.pkl`), pas de serveur Java à surveiller, redémarrage sans
rechargement externe. Critères retenus au-delà du F1 : latence et
disponibilité (dépendance au serveur H2O pour fraude-h2o), taille et
portabilité de l'artefact, explicabilité (importance des variables fournie
par H2O Flow, à recalculer du côté FLAML) et coût opérationnel.

## Importance des variables observée dans Flow (fiche GBM_1)

`montant` est très dominant, puis `freq_24h`, `anciennete` et `nuit` —
hiérarchie cohérente avec les modèles des TP 1 à 3.
