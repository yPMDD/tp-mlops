# TP10 — Compte rendu

**Construire, déployer et sécuriser l’API REST du modèle de détection de fraude**

L’exercice a été exécuté sous Windows avec Python 3.11, scikit-learn 1.9.1, FastAPI 0.162.2, Uvicorn 0.54.0 et Docker Desktop. Le fichier `models/model.pkl` a été copié depuis le modèle TP3 commité dans le dépôt. Il correspond à l’artefact utilisé au TP09. Le dossier de Mme Benali donne `fraude=true` et une probabilité de **0,8899** dans Flask, dans les variantes FastAPI et dans le conteneur sécurisé.

Le port 5000 était déjà occupé. Flask a donc été lancé sur le port 5001. Les mesures et les comparaisons de sécurité utilisent l’adresse IPv4 de bouclage `127.0.0.1` pour éviter le délai de repli IPv6 observé avec `localhost` sur cette machine. Les deux conteneurs ont été publiés sur cette même adresse. Pour mesurer le quota complet et rejouer le test d’erreur après l’inondation, le processus HTTPS a été relancé entre les séries.

## Exécution et preuves

| Étape | Résultat constaté | Preuve |
|---|---|---|
| 2 | Les deux services classent Benali comme fraude. Sur `montant=abc`, Flask renvoie 500 et FastAPI 422. | [Capture](captures/etape-02-flask-fastapi.png) |
| 4 | Les trois routes répondent. Un montant négatif ou un champ supplémentaire donne 422, la mauvaise méthode 405 et l’ancienne route 404. Swagger UI renvoie 422 pour un montant de zéro. | [Échanges HTTP](captures/etape-04-http.txt), [Swagger UI](captures/etape-04-swagger.png) |
| 5 | Les cinq tests du sujet passent. | [Pytest](captures/etape-05-tests.txt) |
| 6–7 | Le rechargement du modèle augmente la latence. Deux processus augmentent le débit mesuré. | [Chargement](captures/etape-06-chargement.txt), [Processus](captures/etape-07-processus.txt) |
| 8–10 | Le relais révèle le corps et la clé sur HTTP. Sur HTTPS, les données applicatives sont chiffrées. Le dictionnaire trouve la clé de démonstration `admin` et les 14 essais reçoivent 401 sur l’API sécurisée. | [Relais](captures/etape-09-https.png), [Dictionnaire](captures/etape-10-dictionnaire.png) |
| 11–14 | La clé de démonstration est visible dans l’image `mauvais`. Les six entrées piégées sont refusées par le schéma sécurisé. La requête 61 déclenche la limite et la désactivation du mode debug masque la trace côté client. | [Images](captures/etape-11-secrets.txt), [Validation](captures/etape-12-validation.txt), [Débit](captures/etape-13-debit.txt), [Erreurs](captures/etape-14-erreurs.txt) |
| 15–16 | Le conteneur `root` peut créer le faux modèle. Dans le conteneur sécurisé, l’utilisateur `app` reçoit `Permission denied`. Les logs sécurisés contiennent les métadonnées de prédiction et les codes HTTP. | [Privilèges](captures/etape-15-privileges.png), [Journaux](captures/etape-16-journal.txt) |

Les quatre captures de terminal sont des images générées à partir des sorties obtenues pendant l’exercice. Les transcriptions correspondantes figurent dans le même dossier. Les mesures et les huit comparaisons sont reprises dans le [bilan](bilan-tp10.md).

## Réponses aux neuf questions

1. **Quel service aide le développeur client ?** FastAPI. Son 422 en JSON identifie `body.montant` et explique l’échec de conversion. Le développeur peut corriger la requête. La page HTML 500 de Flask signale un incident serveur sans identifier le champ.

2. **Que signifient 404, 405 et 422 ?** Le 404 de `POST /predict` indique que la route est inconnue. Le 405 de `GET /v1/predict` indique que la route existe et attend la méthode POST. Le 422 indique que les données échouent à la validation, par exemple avec un montant négatif ou le champ supplémentaire `pays`.

3. **Quelles médianes et quel test détecteraient le rechargement ?** La médiane passe de **25,3 ms** avec un chargement au démarrage à **96,5 ms** en rechargeant à chaque appel, soit **3,81 fois** la latence. Les cinq tests portent sur le contrat HTTP et la prédiction, qui restent identiques. Un test de performance répétable, avec un budget de latence ou un seuil de p95, détecterait la régression.

4. **Quels débits et quel effet des workers sur le quota ?** Le débit passe de **37 à 54 requêtes par seconde** avec 20 clients. Chaque worker conserve sa propre fenêtre glissante en mémoire. La limite globale peut donc dépasser 60 requêtes par minute pour une même clé, selon la répartition des appels. Une passerelle ou un compteur partagé permet de tenir un quota commun.

5. **Une clé de 43 caractères est-elle protégée en HTTP ?** Elle reste lisible dans l’en-tête, comme `admin` lors de la capture HTTP. Il faut combiner une clé aléatoire difficile à deviner avec HTTPS et vérifier le certificat côté client.

6. **Comment limiter les tentatives avec de mauvaises clés ?** Les 14 essais reçoivent 401 avant d’atteindre le compteur associé à une clé valide. Une passerelle peut limiter les tentatives par source avant l’authentification, ralentir les échecs répétés et déclencher une alerte sur les séries de 401.

7. **Pourquoi ignorer `.env` à deux endroits ?** `.gitignore` écarte le fichier du suivi Git. `.dockerignore` l’écarte du contexte de construction envoyé à Docker. En production, un coffre à secrets fournit la clé au service au démarrage. Dans ce TP, `--env-file .env` fournit la clé au conteneur lors de son lancement.

8. **Pourquoi une prédiction pour `nuit=7` est-elle dangereuse ?** Le client reçoit un 200 et peut prendre une décision à partir d’une entrée impossible dans le domaine métier. Le résultat paraît normal. Un 500 rend l’échec visible, tandis qu’un 422 indique précisément comment corriger l’entrée.

9. **Où sont appliquées les huit protections ?** Le code vérifie la clé (2), impose le schéma (4), applique le quota par processus (5), garde le mode debug désactivé (6) et choisit les données à journaliser (8). Uvicorn et le certificat assurent HTTPS (1). La gestion des secrets (3) associe la lecture de l’environnement dans le code à l’injection au démarrage et à l’exclusion du contexte Docker. Le Dockerfile applique l’utilisateur sans privilèges (7). En exploitation, la collecte des logs, les alertes et un quota partagé relèvent aussi du déploiement.

## Nettoyage

Les serveurs et le relais ont été arrêtés. Les deux conteneurs de l’exercice et l’image `fraude-api:mauvais` ont été supprimés. Le projet `tp10-api` et l’image locale `fraude-api:securisee` sont disponibles pour les TP11 et TP12. La clé et les certificats locaux restent exclus de Git. [Sortie du nettoyage](captures/etape-17-nettoyage.txt)
