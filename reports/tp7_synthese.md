# TP7 – Synthèse comparative des outils d'automatisation

Retour d'expérience du TP 7 (workflow Prefect, flux Node-RED), exécuté entièrement
en local : serveur Prefect 3.9.0 sur le port 4200, worker `ProcessWorker` sur la
pool `pool-tp`, Node-RED 5.0.9 sur le port 1880.

| Critère                     | Prefect (orchestrateur)                                 | Node-RED (low-code)                                    | CI (GitHub Actions / GitLab CI, vue en cours uniquement) |
|-----------------------------|---------------------------------------------------------|--------------------------------------------------------|----------------------------------------------------------|
| Ce qui déclenche l'exécution| un planning (cron `0 6 * * 1`), la CLI, l'API, un UI Run | un événement : bouton, minuterie (inject 10 s), erreur (catch), message | un push de commit (ou un planning) |
| Qui peut la modifier        | le développeur : le code Python `flow_mlops.py` définit les tâches | n'importe quel profil métier : glisser-déposer des nœuds dans l'éditeur | le développeur : les fichiers YAML du dépôt |
| Que faire en cas d'échec    | l'état Failed est visible dans l'UI, les logs de chaque tâche sont conservés, retentés automatiques (`retries=2`) | l'erreur est attrapée par le nœud `catch`, mise en forme par `change`, affichée et journalisée (`alertes.log`) ; mais exécution ponctuelle : rien ne rejoue automatiquement | l'exécution échouée apparaît dans l'onglet Actions/CI avec le log ; le merge est bloqué jusqu'à correction |
| Comment la versionner       | le code du workflow est commité (le déploiement est recréé après modification) | menus Export → Download → JSON commité (`nodered/flows.json`) ; sans export, le flux n'existe que dans l'interface | le YAML lui-même est versionné dans le dépôt |
| Type de tâche adapté        | traitements récurrents longs en Python (réentraînement, contrôle qualité, promotion) | relier des événements système et humains autour de services existants | vérifier et valider le code à chaque modification (lint, tests, build) |

## Ce que le TP a démontré (mon exécution)

- **Workflow Prefect** : `reentrainement-fraude` en 4 tâches observables
  (rejouer_pipeline → lire_metriques → valider → notifier). Exécution directe :
  F1 0.8636 ≥ 0.82, Completed. Depuis le déploiement `hebdomadaire` (Quick run) :
  `unbiased-camel` prélevé par le worker puis Completed.
- **Arrêt sur règle de qualité** : `max_depth: 12 → 2`, le workflow s'arrête exactement
  à `ValueError: F1 0.2013 < seuil 0.82 : modele refuse` (run `resourceful-oyster`,
  Failed et visible en rouge dans l'UI) ; retour au vert après restauration des
  paramètres grâce au cache DVC (aucun réentraînement, même F1).
- **Planification** : déploiement `reentrainement-fraude/hebdomadaire`
  (id `97155a66-31ae-4594-b53a-eb75b23446a9`), cron « 0 6 * * 1 » = lundi 6 h,
  worker `ProcessWorker` prêt sur la pool `pool-tp`.
- **Flux 1 Node-RED** : un clic sur le bouton inject crée une exécution via
  l'API Prefect ; barre Debug : « Exécution miniature-sidewinder créée, état :
  Scheduled » puis le worker termine en Completed quelques secondes plus tard.
- **Flux 2 Node-RED** : toutes les 10 s, une transaction (8500 MAD, nuit) est
  envoyée au modèle FLAML en service (port 8101) ; le switch route la prédiction 1
  vers « Transaction suspecte : 8500 MAD la nuit ». Quand le service est coupé,
  le catch horodate l'incident : `2026-10-28T02:45:17.014Z ALERTE service du
  modele indisponible : RequestError: connect ECONNREFUSED 127.0.0.1:8101`,
  affiché dans Node-RED et ajouté dans `reports/alertes.log`. Au redémarrage du
  service, les alertes cessent et les appels reviennent à 200 OK.

## Conclusion

Prefect exécute et surveille des **traitements récurrents écrits en Python** ;
Node-RED **branche** ces traitements sur des événements (un bouton, une minuterie,
une erreur) sans code ; une chaîne CI **valide le code** à chaque modification.
Les trois sont complémentaires : la CI protège le dépôt, Prefect pilote le
pipeline MLOps, Node-RED connecte ce pipeline aux utilisateurs non-développeurs
et aux services eux-mêmes.
