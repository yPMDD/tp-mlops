# Phase A — Projet, Git et données

## A1 — Exclusions Git

`git check-ignore -v -- .venv/ mlruns/` affiche la règle de `.gitignore` qui couvre chacun des deux répertoires. `git ls-files -- .venv mlruns` ne renvoie aucun fichier suivi. Ces commandes contrôlent les ajouts Git ordinaires. Un ajout forcé contournerait `.gitignore`.

Preuve dans [la sortie Git](a1-git-check-ignore.txt).

## A2 — Provenance du classeur

Le fichier XLSX téléchargé depuis le [portail officiel](https://data.gov.ma/data/fr/dataset/referentiel-des-medicaments) mesure **530 243 octets**. Son MD5 est `68a57c72d5eeb4c5256fba3322393d32`. Le CNOPS publie ce jeu sous **Open Data Commons Open Database License (ODbL)**. La fiche indique le **13 décembre 2021 à 16 h 26 UTC** pour la dernière modification du jeu. Le portail date séparément la modification de la ressource XLSX du **18 décembre 2017 à 20 h 26 UTC**.

Preuves dans [les métadonnées du portail](a2-portail.json) et [la sortie de l'audit](a2-a5-mesures.txt).

## A3 — Dimensions et cible

Le classeur comporte **5 917 présentations** et **12 colonnes**, hors en-tête. Parmi elles, **1 977** ont un taux de remboursement de `0 %`, soit **33,41 %**.

## A4 — Dosages

`DOSAGE1` compte **181 cellules vides** et **946 valeurs non convertibles en un seul nombre**, cellules vides comprises. `1 / 125` en `G / MG` représente des doses de 1 g et 125 mg. `100 / 12.5` et `500 / 62.5`, en `MG / MG`, donnent chacun les doses en mg de deux composants. Les remplacer par zéro perd la quantité de chaque composant et confond les dosages composés avec les dosages absents ou réellement nuls dans la variable préparée.

## A5 — Présentations par DCI

**AMOXICILLINE** est la DCI la plus fréquente avec **157 présentations**. Le nombre de présentations d'une même DCI peut refléter la variété de dosages, de formes ou de produits disponibles pour une molécule. Cette information pourrait être liée à sa couverture et doit être évaluée sur le jeu de test.

## A6 — Découpage stratifié

La graine G, obtenue à partir des quatre derniers chiffres du matricule, vaut 64. La stratification conserve la proportion globale de classe 1 dans le jeu de test, à l'arrondi près. Le médicament est sélectionné au rang G modulo 1977 dans le classeur brut, parmi les présentations non remboursées.

A6  Entrainement : 4437 | Test : 1480
A6  Classe 1 dans le test : 495 (33.45%)
A6  Variables : ppv, ph, prix_br, ecart_br, dosage, generique, nb_meme_dci, injectable, comprime
Medicament personnel, rang 64 : SOLIAN 100 MG/ML (CODE 6118010120312)
