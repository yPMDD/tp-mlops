# TP 1 — Découvrir la boîte à outils MLOps
## Compte rendu

**Binôme :** _à compléter_ — **Date :** 28/09/2026
**Environnement :** Windows 11, Python 3.14, MLflow 3.16.1, DVC 3.67.1, scikit-learn

---

### Résultat de la série d'exécutions

| Exécution | n_estimators | max_depth | f1_test | Durée |
|---|---|---|---|---|
| rf-100-4   | 100 | 4  | 0.6634 | 5,8 s |
| rf-200-8   | 200 | 8  | 0.8549 | 6,3 s |
| rf-300-12  | 300 | 12 | 0.8636 | 6,8 s |
| **rf-500-16** | **500** | **16** | **0.8669** | **7,8 s** |
| rf-600-24  | 600 | 24 | 0.8636 | 8,3 s |

Le gain se raréfie après 300 arbres : passer de 300 à 500 arbres ne rapporte que
+0,003 de F1 pour +1 s d'entraînement, et 600 arbres est **moins bon** que 500
(0,8636 contre 0,8669). Le modèle promu est donc `rf-500-16`, enregistré en
version 1 de `fraude-tp1` avec l'alias `@production`.

---

### 1. Paramètre ou métrique : quelle différence ?

Un **paramètre** est une **entrée de la commande** : une valeur que l'on choisit
*avant* d'entraîner, et que l'on pourrait changer sans changer de code.
Un **métrique** est une **mesure calculée après coup** sur le jeu de test, qui
sert à comparer les exécutions entre elles. Un paramètre se saisit, une métrique
se lit.

*Exemple de paramètre* : `n_estimators = 500` — plus la forêt est grande,
plus le modèle est flexible : nous choisissons de faire voter 500 arbres. Il est modifiable sans réécrire une ligne.
*Exemple de métrique* : `f1_test = 0.8669` — elle n'existe qu'après
l'entraînement, sur les 25 % de données réservées au test, et elle seule permet
de classer les cinq exécutions.

Dans MLflow les deux sont stockés dans des tables séparées (`params` et
`metrics`). Les paramètres sont les hyperparamètres que `autolog()`
capture tout seul ; les métriques de test, elles, doivent être journalisées
explicitement — c'est ce que fait `mlflow.log_metric('f1_test', f1)`. Sans cette
ligne, on aurait les métriques d'entraînement mais aucune base de comparaison
honnête.

> Une nuance observée pendant le TP : `autolog()` journalise des métriques
> nommées `training_*` (précision, rappel, ROC AUC). Elles valent **0.99 à 1.00**
> alors que `f1_test` plafonne à 0.87. Elles sont calculées sur les données
> d'entraînement, donc déjà vues par le modèle : s'en servir pour comparer deux
> exécutions donnerait l'illusion d'un modèle bien meilleur qu'il ne l'est.

---

### 2. F1 proches, durées différentes : laquelle promouvoir ?

Sur nos données, `rf-300-12` et `rf-600-24` obtiennent **exactement le même
F1 = 0.8636**, pour 6,8 s et 8,3 s. Je **`rf-300-12`**, pour trois raisons :

- **À métrique égale, le plus simple gagne.** 300 arbres au lieu de 600 : le
  modèle est deux fois plus rapide à entraîner *et* à prédire, deux fois plus
  petit en mémoire, et tout aussi juste. C'est le principe du rasoir d'Occam
  appliqué à un modèle.
- **Le surcoût de temps se paie à chaque inférence.** 2,5 s gagnées à
  l'entraînement ne se retrouvent pas en production : chaque requête de
  détection de fraude traverse les 600 arbres au lieu de 300.
- **La différence de F1 n'est pas le seul critère.** À 0,003 près, l'écart est
  dans le bruit de l'échantillon de test. Conclure « 500 arbres sont meilleurs »
  sur cette base serait une erreur de méthode : il faudrait un test répété avec
  d'autres `random_state` pour le prouver.

Ici, la meilleure exécution reste `rf-500-16` (F1 = 0.8669) : son gain de
+0,003 est faible, mais sa durée reste inférieure à celle de `rf-600-24`. Dans
un cas réel, on aurait probablement fixé un seuil de F1 minimal en deçà
duquel on privilégie systématiquement le modèle le moins coûteux.

---

### 3. Pourquoi un alias plutôt qu'un numéro de version ?

Le service d'inférence ne doit pas connaître les détails du cycle de vie des
modèles. Avec `models:/fraude-tp1/1`, le code **fige** la version 1 dans la
ligne source. Chaque nouvelle promotion obligerait à modifier le code, le
redéployer, et le tester — donc à faire tomber le service en production à chaque
entraînement.

Avec l'alias :

```python
m = mlflow.pyfunc.load_model('models:/fraude-tp1@production')
```

le code ne dit jamais quel modèle il utilise : il demande « le modèle
actuellement en production ». MLflow résout `@production` en version 1 au
chargement. Le jour où l'équipe entraîne une version 2 meilleure et exécute
`set_registered_model_alias(..., 'production', 2)`, le servicechargera la
version 2 **sans une seule ligne de code modifiée**.

Autrement dit : le numéro de version identifie un modèle, l'alias désigne un
*rôle*. Séparer les deux permet de faire évoluer la production indépendamment du
code. C'est aussi ce qui rendra le déploiement possible au TP 10.

---

### 4. Que contient le `.dvc`, et pourquoi Git ne suit pas le CSV ?

`data/transactions.csv.dvc` pèse **102 octets** pour un fichier de données de
**85 902 octets**. Il contient uniquement les métadonnées de suivi :

```yaml
outs:
- md5: cf9f6f86c141e7df32c61715c493483f
  size: 85902
  hash: md5
  path: transactions.csv
```

C'est un **pointeur** : l'empreinte MD5 du contenu, sa taille, l'algorithme de
hachage et l'emplacement du fichier. Il ne contient **aucune donnée**.

Git ne doit pas suivre le CSV lui-même pour trois raisons :

- **La taille.** Git stocke chaque version en base dans `.git/objects/`. Le jour
  où le jeu de données est régénéré, corrigé ou remplacé par une version plus
  riche, l'ancienne version reste dans l'historique : le dépôt gonfle à chaque
  commit alors qu'une seule version est utile.
- **L'inutilité du diff.** Git est conçu pour comparer du **texte**. Sur un CSV,
  une seule ligne modifiée produit un diff de la totalité du fichier, illisible.
- **Le rôle de DVC.** DVC prend le relais sur les fichiers volumineux : il
  calcule le MD5, l'ajoute à `.gitignore`, et ne fait suivre par Git que le
  pointeur. On peut ainsi épingler précisément une version des données.

Concrètement : `git checkout` + `dvc pull` restitue le jeu de données **exactement
identique** à celui qui a servi à entraîner, ce qui est la vraie garantie de
reproductibilité — bien meilleure qu'un fichier que Git promettrait de
restaurer.

---

### 5. Deux informations à journaliser en plus pour être reproductible

**a) L'empreinte et la version du jeu de données.** Un `f1_test` sans dire
*sur quelles données* il a été calculé ne veut rien dire. Il faudrait journaliser
le MD5 du CSV (que DVC connaît déjà : `cf9f6f86c141e7df32c61715c493483f`) et
éventuellement sa version. Sans cela, impossible de détecter qu'un jeu de données
a changé entre deux exécutions alors que les hyperparamètres sont identiques.

**b) La durée d'exécution et les versions des bibliothèques.** MLflow 3 propose
la métrique `mlflow.execution_duration.ms` ; il faudrait aussi journaliser
`scikit-learn`, `numpy` et `pandas` dans des tags, par exemple :

```python
import sklearn, numpy, pandas
for nom, mod in [('sklearn', sklearn), ('numpy', numpy), ('pandas', pandas)]:
    mlflow.log_param(f'env.{nom}', mod.__version__)
```

Cela documente la réponse à la question 2 : on ne peut arbitrer entre deux
exécutions que si l'on sait combien de temps elles ont pris. Et une
reproductibilité exige de savoir avec quelles versions de scikit-learn le
modèle a été entraîné, car le comportement de `RandomForestClassifier` a évolué
d'une version à l'autre.

> *Accessoirement, l'ignorance de ces deux informations nous a fait perdre du
> temps pendant ce TP : deux exécutions rf-200-8 strictement identiques ont été
> lancées, et rien dans l'interface ne distinguait la première de la seconde.*

---

### Écart avec l'énoncé, à signaler

L'énoncé demande d'enregistrer le modèle via `runs://<RUN_ID>/model`. Cette URI
**ne fonctionne plus en MLflow 3.16** : `autolog()` n'écrit plus le modèle dans
le dossier de l'exécution, mais dans un *LoggedModel* séparé
(`mlartifacts/1/models/m-<id>/`). Nous avons donc utilisé l'URI
`models:/m-<id>`, en résolvant l'identifiant du modèle depuis le Run ID de la
meilleure exécution. Le résultat est identique : modèle enregistré, alias posé,
rechargement par alias et prédiction correcte.

---

### Reste à faire

- [ ] Captures d'écran : comparaison des 5 exécutions (onglet *Compare*)
- [ ] Capture d'écran : onglet *Models* montrant `fraude-tp1` version 1 et son alias `@production`
- [ ] Premier commit Git
