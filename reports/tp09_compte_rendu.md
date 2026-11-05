TP9 – Compte rendu et mesures

1. Image et conteneur
Une image Docker est le modèle construit à partir du Dockerfile, des dépendances, du code et du modèle. Un conteneur est une instance de cette image en cours d’exécution. Après une modification de api/main.py, il faut reconstruire l’image puis recréer le conteneur à partir de cette nouvelle image ; modifier le fichier sur le disque ne change pas le conteneur existant.

2. Versions des dépendances
Les opérateurs == figent les versions utilisées pour construire l’environnement. Le modèle TP3 a été entraîné avec scikit-learn 1.9.1. Une autre version peut modifier le format de sérialisation ou le comportement des estimateurs et empêcher le chargement ou changer les prédictions.

3. Cache Docker
Mesures avec Measure-Command sur cette machine : Dockerfile bien ordonné, 6,70 s ; Dockerfile.mauvais, première reconstruction 61,77 s et seconde reconstruction après une nouvelle modification du code 66,14 s. Dans le Dockerfile bien ordonné, requirements.txt est copié et pip install est exécuté avant le code ; changer api/main.py laisse donc ces couches en cache. Avec COPY . . avant pip install, chaque changement de code invalide la couche COPY et force la réinstallation des dépendances. Les temps dépendent de la machine et du réseau.

4. RUN, CMD et accès réseau
RUN exécute une commande pendant la construction de l’image (ici, installer les dépendances). CMD indique la commande lancée au démarrage du conteneur (ici, Uvicorn). --host 0.0.0.0 fait écouter Uvicorn sur toutes les interfaces du conteneur. EXPOSE documente le port ; il ne publie pas à lui seul le port sur l’hôte. docker run -p 8000:8000 réalise cette publication.

5. Deployment, Service et étiquette
Le Deployment maintient le nombre de pods demandé et les remplace si nécessaire. Le Service fournit une adresse stable dans le cluster et répartit le trafic vers les pods sélectionnés. L’étiquette app: fraude-api relie les pods au sélecteur du Service et du Deployment. Avec le sélecteur app: fraude, le Service ne trouverait aucun pod correspondant et n’aurait pas de backend utilisable.

6. Readiness
Un pod apparaît d’abord en 0/1 pendant son démarrage ; il passe à 1/1 lorsque le conteneur est prêt. La readinessProbe appelle /health et empêche le Service d’envoyer du trafic avant la disponibilité. Sans elle, un pod 2.1 qui plante au chargement du modèle pourrait recevoir des requêtes avant que Kubernetes l’écarte, provoquant des erreurs côté client.

7. Mise à jour 2.0 et preStop
Pendant le test de 40 secondes à l’étape 18, le client a compté 0 erreur. Il a d’abord reçu v1.0, puis un mélange de v1.0 et v2.0 pendant le remplacement progressif, puis v2.0. preStop exécute sleep 5 avant l’arrêt du conteneur afin de laisser le temps aux requêtes en cours de se terminer pendant le retrait du pod du trafic.

8. Avantage / mesure obtenue

| Avantage | Mesure obtenue |
|---|---|
| Cohérence | La prédiction de Mme Benali est 0,8899 dans le modèle local, Docker et Kubernetes, avec scikit-learn 1.9.1. |
| Portabilité | fraude-api:1.0 a été sauvegardée puis rechargée ; l’identifiant SHA256 avant/après est identique. Archive : 150,9 MiB. kind a chargé cette image locale. |
| Évolutivité et auto-réparation | Le Deployment a servi avec 2 puis 4 pods. Le client a reçu des réponses de 4 pods avec 0 erreur. Après suppression d’un pod, Kubernetes l’a recréé et est revenu à 4/4 prêts ; le Deployment a ensuite été ramené à 2 réplicas. |

Résultats observés
- Docker : /health HTTP 200, /predict HTTP 200 avec probabilite=0.8899, requête incomplète HTTP 422, /docs HTTP 200.
- Kubernetes : /predict a renvoyé probabilite=0.8899 ; client baseline et client v2.0 sans erreur.
- Version 2.1 : échec au démarrage avec FileNotFoundError pour models/modele.pkl ; timeout du rollout à 40 s ; le client n’a reçu que v2.0 avec 0 erreur pendant 50 s ; rollout undo a rétabli v2.0.
- Le code API a été restauré à VERSION = "1.0" et models/model.pkl après l’exercice.
