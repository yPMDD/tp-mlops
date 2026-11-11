# Phase B — Versionnement et pipeline

## B1 — Classeur suivi par DVC

Git suit le pointeur du classeur, le fichier d'exclusion du répertoire et la configuration DVC. Le pointeur contient le MD5 **68a57c72d5eeb4c5256fba3322393d32**, identique à A2. [Sortie et pointeur](b1-suivi-dvc.txt)

## B2 — Stockage local

Le stockage `../stockage-dvc` contient des objets sous `files/md5/`. Les deux premiers caractères de l'empreinte servent de sous-répertoire. DVC retrouve le nom logique à partir du pointeur Git et stocke le contenu par empreinte pour dédupliquer les objets. [Configuration et poussée](b2-stockage-dvc.txt)

## B3 — Deux versions et restauration

La V2 conserve **5 709 présentations** dans l'ordre du classeur, après retrait des **208** lignes à PPV nul. Les tags sont `donnees-v1` et `donnees-v2`. La V2 est un classeur dérivé et le fichier V1 d'origine est conservé à son chemin initial. Pour prouver la restauration, la copie de travail a été mise à l'écart, puis `git switch --detach donnees-v1` et `dvc pull data/brut/ref-des-medicaments-cnops-2014.xlsx.dvc` ont été exécutés. Les empreintes SHA-256 sont identiques. [Preuve de restauration](b3-versions.txt)

## B4 — Graphe et responsabilités

| Étape | Dépendances | Paramètres | Sorties |
|---|---|---|---|
| Préparer | Classeur et scripts de préparation | Source, version, graine, part de test, chemins CSV | Jeux d'entraînement et de test |
| Entraîner | CSV d'entraînement et scripts de la forêt | Graine, arbres, profondeur, chemins | Modèle sérialisé |
| Évaluer | CSV de test, modèle et scripts de mesure | Seuil F1, chemins | F1, précision et rappel de classe 1 |

[Graphe DVC](dvc-dag.txt) · [Configuration des étapes](../dvc.yaml)

## B5 — Invalidation du cache

Le second `dvc repro` signale que le pipeline est à jour. Passer de 12 à 16 relance l'entraînement et l'évaluation. Le classeur, la graine et la part de test restent identiques, donc la préparation conserve ses sorties. Le retour à 12 réutilise les résultats en cache. [Sorties de reproduction](b5-repro.txt)

## B6 — Expériences

| Profondeur | F1 classe 1 |
|---:|---:|
| 8 | 0,696855 |
| 12 | 0,768683 |
| 16 | 0,783217 |

La profondeur **16** donne le meilleur F1 mesuré sur ce test, avec environ 0,0145 de mieux que 12. Elle est retenue dans la comparaison B6. Les expériences temporaires laissent les valeurs de `params.yaml` identiques au commit de référence. Le modèle de référence des phases suivantes garde la profondeur **12** imposée. [Résultats détaillés](b6-experiences.csv)

## B7 — Validation

La préparation vérifie la présence des 12 colonnes, la validité des prix (finis et non négatifs) et les valeurs de remboursement autorisées (0 % ou 70 %). Elle contrôle aussi la présence de lignes et les statuts P/G. Sur la copie privée de la colonne PPV, le validateur renvoie le code 1 et le message « Validation refusee : colonnes manquantes : PPV ». [Sortie du validateur](b7-validation.txt)

## B8 — Profondeur 2

L'expérience forcée réexécute validation, préparation, entraînement et évaluation. Le **F1 de classe 1 vaut 0,344948**, sous le seuil **0,65** lu dans `qualite.f1_min` de `params.yaml`. DVC conserve l'évaluation pour la preuve et le modèle est déclaré non admissible au registre. [Journal du pipeline](b8-profondeur-2.txt)

### Vérification après la phase C

Une réextraction Git sous Windows avait changé la fin de ligne de valider.py sans changer son contenu. Les règles de .gitattributes fixent la fin de ligne LF des scripts et fichiers YAML, de sorte que DVC conserve les mêmes empreintes pour un même code. [Deux reproductions après normalisation](b5-portabilite.txt)
