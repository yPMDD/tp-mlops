# Phase C — Suivi, registre et service

## C1 — Exécutions sur les données V2

| Modèle | F1 classe 1 | Précision | Rappel |
|---|---:|---:|---:|
| Forêt, profondeur 8 | 0,696855 | 0,814706 | 0,608791 |
| Forêt, profondeur 12 | 0,768683 | 0,835052 | 0,712088 |
| Forêt, profondeur 16 | 0,783217 | 0,833747 | 0,738462 |
| Régression logistique | 0,500692 | 0,675373 | 0,397802 |

Les quatre exécutions réussies partagent le même jeu de test et journalisent leurs paramètres, leurs métriques et leur modèle. Le premier essai de sérialisation de la forêt a échoué. Les quatre résultats du tableau proviennent des exécutions terminées après avoir déclaré explicitement le type scikit-learn des arbres formés localement. [Identifiants et métriques](c1-metriques.csv)

## C2 — Comparer les réglages

Dans la vue de comparaison MLflow, le **graphique à coordonnées parallèles** peut relier le paramètre `profondeur` à la métrique `f1`. On sélectionne les trois forêts en conservant la graine, les données et les 200 arbres identiques. C'est la profondeur qui varie entre ces essais. Le F1 augmente de 0,0864 de 8 à 16, surtout parce que le rappel monte de 0,6088 à 0,7385. La régression logistique est un comparatif de famille de modèles et ne possède pas de profondeur. [Guide MLflow et graphique](https://mlflow.org/blog/tune-and-benchmark-with-mlflow/)

L'accès de l'assistant au navigateur local a été refusé. La preuve jointe est un graphique calculé à partir des quatre exécutions journalisées. [Graphique F1 et profondeur](c2-f1-profondeur.png)

## C3 — Signature du modèle de référence

La signature du modèle V2 à profondeur 12 comporte **neuf entrées obligatoires**. `ppv` est de type **double** et `generique` de type **long**. Le service applique ce schéma avant la prédiction, ce qui permet de rejeter une entrée manquante ou incompatible. L'exemple d'entrée est enregistré avec le modèle. [Signature et exemple issus de MLflow](c3-signature.json)
