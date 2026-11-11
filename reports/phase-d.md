# Phase D — AutoML et low-code

Le classeur V1 est commun aux trois approches, car Orange part du XLSX brut. Les 4 437 lignes d'entraînement et 1 480 lignes de test proviennent du même découpage stratifié avec G. Le F1 concerne la classe 1.

## D1 — FLAML à 60 secondes

FLAML sélectionne **LightGBM**. Son F1 de test est **0,889340**, contre **0,769902** pour la forêt de référence V1, soit un gain de 0,1194 sur ce test. Le budget FLAML sert à optimiser le F1 pendant la recherche. [Exécution FLAML](d1-flaml.json) · [Référence V1](c4-execution-v1.json)

## D2 — FLAML à 120 secondes

LightGBM reste en tête et le F1 de test passe à **0,890467**, soit **+0,001127**. Une recherche plus longue explore davantage de réglages et optimise la validation interne. Le score sur les lignes de test peut augmenter, stagner ou baisser. [Exécution FLAML](d2-flaml.json)

## D3 — H2O AutoML

Le meilleur modèle est **GBM_4** dans la session enregistrée. Le classement utilise l'**AUC**, qui vaut **0,930957** en tête du leaderboard. Son **F1 sur le test tenu à l'écart est 0,845996**. Les réseaux de neurones et les ensembles empilés sont exclus pour que la limite de **10 modèles** s'applique au leaderboard complet. [Résultats](d3-h2o.json) · [Classement H2O](d3-classement-h2o.csv)

## D4 — Registre et latence

Le LightGBM FLAML de 120 s est enregistré sous `remboursement-automl@production` et sert sur **8100**. Les deux services ont reçu la même requête après un appel d'échauffement chacun, puis **50 appels séquentiels par service**. La latence HTTP médiane mesurée sur cette machine est de **22,92 ms** pour la forêt (8000) et **7,11 ms** pour LightGBM (8100). [Registre](d4-registre.json) · [Mesures brutes](d4-latences.json)

## D5 — Workflow Orange

Le widget File lit le XLSX brut. Le workflow conserve en métas `CODE`, `NOM`, `DCI1`, `UNITE_DOSAGE1`, `PRESENTATION` et `FORME` pour identifier et interpréter les lignes. DCI et forme contribuent aux variables dérivées. Les valeurs brutes de `DOSAGE1`, des prix et de `PRINCEPS_GENERIQUE` sont remplacées par les variables prescrites. `TAUX_REMBOURSEMENT` sert uniquement à créer la cible discrète. Les scripts de branche partagent les mêmes indices stratifiés calculés avec G.

| Apprenant Orange | AUC | F1 classe 1 |
|---|---:|---:|
| Forêt aléatoire | 0,924010 | 0,769902 |
| Régression logistique | 0,803811 | 0,530414 |
| Naive Bayes | 0,799920 | 0,604797 |

Le tableau reprend les résultats du widget Test and Score en mode test séparé et le F1 de la classe 1. [Workflow Orange](../orange/remboursement.ows) · [Mesures Orange](d5-orange.json) · [Rejeu du Canvas](d5-canvas.json)

## D6 — Faux négatifs

La forêt, meilleure par AUC et F1, manque **142 présentations non remboursées**. Sa matrice met les classes réelles en lignes et les classes prédites en colonnes.

| Classe réelle | Prédite 0 | Prédite 1 |
|---|---:|---:|
| 0 | 916 | 69 |
| 1 | 142 | 353 |

[Matrices mesurées](d5-orange.json)

## D7 — Choix pour la production

Le code avec DVC rend la forêt déterministe à graine et environnement constants. MLflow lie paramètres, données et modèles pour les deux AutoML. FLAML a le meilleur F1 observé et la plus faible latence, mais un budget en secondes dépend des ressources du poste. H2O a un budget en modèles et expose son leaderboard. Orange fournit un workflow visuel et une matrice facilement inspectable. Les fichiers, versions et paramètres d'Orange doivent être archivés pour rejouer l'expérience.

Je retiendrais **LightGBM FLAML** comme candidat d'après ces mesures, avec sa version et son environnement figés. Avant une décision réelle, je vérifierais que les entrées sont disponibles à la date de décision et j'évaluerais la qualité sur des données séparées dans le temps. [Comparaison des résultats](d4-registre.json)
