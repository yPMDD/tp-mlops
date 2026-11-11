# Fiche modèle — Remboursement CNOPS

## Identité et usage

La forêt de référence V1 du projet pédagogique est enregistrée sous `remboursement-rf`, version 1 et alias `production`. Elle estime la probabilité qu'une présentation du référentiel soit non remboursée (classe 1). Elle sert à illustrer le tri de dossiers et l'explicabilité. La décision de remboursement reste du ressort du gestionnaire.

## Données et entraînement

Le référentiel CNOPS provient du portail Open Data du Maroc sous licence ODbL. La V1 contient 5 917 présentations, dont 1 977 de classe 1. La forêt comporte 200 arbres de profondeur maximale 12. Le découpage stratifié 75/25 utilise la graine G du matricule. Les neuf variables sont fixées dans `src/preparer.py`. Les valeurs vides ou composées de dosage deviennent 0. Le taux de remboursement sert à fabriquer la cible.

## Résultats

Sur les 1 480 lignes de test V1, le F1 de la classe 1 est **0,769902**, la précision **0,836493** et le rappel **0,713131**. La règle de qualité est F1 ≥ 0,65. Le seuil utilisé pour lire la prédiction de classe dans l'audit est 0,5. Les sorties de suivi figurent dans `reports/c4-execution-v1.json`.

## Explicabilité, équité et disponibilité des entrées

La permutation sur le test place `nb_meme_dci` et `dosage` en tête. L'explication du dossier personnel réconcilie base et contributions avec la probabilité. Les taux de fausses alertes sont de 11,32 % pour les princeps et 3,74 % pour les génériques. Retirer `generique` réduit légèrement cet écart. Pour prédire avant la décision, il faut vérifier la disponibilité de `PRIX_BR` et supprimer `prix_br` et `ecart_br` si la base n'est pas encore connue. Cette ablation change le F1 de 0,769902 à 0,769231 sur le test.

## Limites et surveillance

Le référentiel historique ne permet pas de mesurer la dérive temporelle ni de garantir la validité pour une nouvelle molécule. Les prix, le dosage, la composition du référentiel et la prévalence peuvent évoluer. Il faut valider sur une période ultérieure, contrôler le schéma et les taux d'erreurs par groupe, puis expliquer les décisions individuelles. Le flux de réentraînement propose les modèles admissibles sous `staging` et applique un contrôle des variables avant l'enregistrement.
