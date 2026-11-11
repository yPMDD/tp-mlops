# TP 10 - Bilan

## Mesures (etapes 6 et 7)

| Mesure | req/s | mediane | p95 |
|---|---:|---:|---:|
| Modele charge une seule fois (200 requetes, 1 client) | 31 | 25.3 ms | 48.2 ms |
| Modele recharge a chaque appel (200 requetes, 1 client) | 10 | 96.5 ms | 123.4 ms |
| 1 processus, 20 clients (400 requetes) | 37 | 531.7 ms | 629.1 ms |
| 2 processus, 20 clients (400 requetes) | 54 | 358.6 ms | 576.5 ms |

## Securite (etapes 9 a 16)

| Pratique | Attaque | Brouillon | Version securisee |
|---|---|---|---|
| 1 HTTPS | Relais espion | Le corps JSON et `X-API-Key: admin` sont lisibles. | Trafic TLS chiffre. Le client obtient 200 et 0.8899. |
| 2 Cle d'API | Dictionnaire | `admin` donne 200 au 11e essai. | 14 reponses 401. |
| 3 Secrets | Lecture du code, `docker history` et `printenv` | Cle dans le code du brouillon et cle de demonstration dans l'image `mauvais`. | Le code lit l'environnement. L'image ne contient aucune valeur `API_KEY`. |
| 4 Validation | Six entrees piegees | 3 reponses 200 et 3 reponses 500. | 6 reponses 422. |
| 5 Limite de debit | 100 requetes authentifiees | 100 reponses 200. | 60 reponses 200 et 40 reponses 429 avec une fenetre vide. |
| 6 Erreurs discretes | `montant=abc` | HTTP 500 avec trace en mode debug. Apres correction, HTTP 500 generique. | HTTP 422 sans trace. |
| 7 Sans privileges | `whoami` et `touch` dans `models/` | `root` cree `modele_pirate.pkl`. | `app` recoit `Permission denied`. |
| 8 Journal | Lecture des logs | La cle `admin` et le corps de la transaction sont journalises. | Le journal de prediction contient l'identifiant, la version, la probabilite et la duree. Les logs d'acces montrent les 401, 422 et 429. |
