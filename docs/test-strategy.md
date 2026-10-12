# Stratégie de test — QuickOrder V3.1

| | |
|---|---|
| Version testée | QuickOrder V3.1 (Flask / Flask-SQLAlchemy / SQLite) |
| Nature | Audit QA pré-production, campagne initiale sans modification de `app/` |
| Documents liés | `risk-matrix.md`, `test-cases.xlsx`, `execution-report.md`, `bug-reports/` |

> Convention de lecture : les éléments de la section 13 sont des **indices observés à la lecture du code source** (`app/`). Ce sont des hypothèses à confirmer par un test exécuté ; aucun n'est présenté ici comme un défaut prouvé. Le but de la campagne est de *prouver* (capture, requête/réponse, console), pas de supposer.

## 1. Objectif et contexte

Évaluer si QuickOrder, plateforme de commande de repas, peut être mise en production. La stratégie définit ce qui est testé, comment, avec quels outils et selon quels critères la décision Go / No-Go sera prise. L'application est pédagogique : le README indique que certaines anomalies sont conservées volontairement pour créer des situations de test réalistes.

## 2. Périmètre

### 2.1 Fonctionnel (interface web)

| Domaine | Éléments |
|---|---|
| Authentification et session | Inscription, connexion, déconnexion, « se souvenir de moi », paramètre `next`, accès aux pages protégées, rôles client / admin |
| Catalogue | Liste des restaurants, recherche, filtre catégorie, filtre végétarien, filtre frais de livraison, tris (note, prix, délai), page restaurant, filtre produits |
| Panier | Ajout, modification de quantité, suppression, vidage, règle mono-restaurant, persistance en session |
| Coupons | Code, expiration, minimum de commande, plafond de réduction, insensibilité à la casse |
| Checkout et paiement | Choix d'adresse, modes `card`, `paypal`, `cash`, calcul du total, rendu de monnaie, note client |
| Commandes | Liste, filtre par statut, détail, annulation client, « recommander » |
| Stock et disponibilité | Produit indisponible, stock à 0, stock insuffisant, décrément du stock |
| Restaurant fermé | Comportement du panier, du checkout et de l'API quand `is_open` est faux |
| Avis et favoris | Dépôt d'avis (note 1 à 5 + commentaire), bascule de favori |
| Profil | Mise à jour du nom et du téléphone, gestion des adresses (ajout, défaut, suppression) |
| Administration | Tableau de bord, changement de statut d'une commande, contrôle d'accès |

### 2.2 API REST (préfixe `/api`, en-tête `X-API-Key`)

`GET /health`, `GET /restaurants` (+ `q`, `category`, `min_rating`), `GET /restaurants/{id}`, `GET /restaurants/{id}/products`, `GET /products/{id}`, `POST /coupons/validate`, `POST /orders`, `GET /orders` (+ `status`), `GET /orders/{id}`, `POST /orders/{id}/cancel`, `GET /favorites`. Contrat décrit par `openapi.yaml` et Swagger UI.

### 2.3 Transverses

- Sécurité applicative de premier niveau (authentification, autorisation, CSRF, redirection, exposition de données) : vérifications QA, pas un test d'intrusion.
- Intégrité des données : cohérence totaux / lignes / stock, doublons de commandes.
- Utilisabilité de base et messages d'erreur ; compatibilité limitée à un navigateur Chromium.
- Santé de l'application : `/health` et `/api/health`.

## 3. Hors périmètre

- Reconstruction ou correction du code source pendant la campagne initiale (les correctifs éventuels sont proposés dans une branche séparée).
- Passerelle de paiement réelle : le paiement est simulé (dans `build_order`, `payment_ok` est fixé à vrai).
- Tests de charge, de performance à grande échelle, montée en charge de SQLite.
- Test d'intrusion complet, revue de l'infrastructure (Docker, réseau, TLS).
- Compatibilité multi-navigateurs / mobile exhaustive, accessibilité WCAG complète (constats ponctuels seulement).
- Envoi d'emails ou de notifications (non présents dans le code lu).
- Revue exhaustive de la CSS et du contenu éditorial.

## 4. Parcours critiques

Classés par criticité métier (argent, chiffre d'affaires, confiance client).

| ID | Parcours | Étapes clés | Pourquoi critique |
|---|---|---|---|
| PC1 | Commande nominale web | Connexion, restaurant, ajout panier, checkout, paiement, détail commande | Cœur de la valeur, flux monétaire |
| PC2 | Paiement | `card`, `paypal`, `cash` (montant suffisant / insuffisant) | Risque financier direct, doublons |
| PC3 | Coupon et calcul du total | Validation, minimum, expiration, plafond, arrondi | Impact sur le montant facturé |
| PC4 | Stock et disponibilité | Produit à 0, quantité supérieure au stock, produit indisponible | Promesse non tenable au client |
| PC5 | Restaurant fermé / minimum de commande | Commande refusée ou acceptée à tort | Cohérence métier |
| PC6 | Commande par API | `POST /api/orders` avec ou sans clé, utilisateur par défaut | Surface d'intégration, authentification |
| PC7 | Annulation et statuts | Annulation client, transitions admin | Intégrité du cycle de vie des commandes |
| PC8 | Authentification, session, redirection | Login, `next`, logout, accès non autorisé | Sécurité et confidentialité |
| PC9 | Recherche et filtres | Recherche, filtre livraison, végétarien, tris | Découverte, première interaction |
| PC10 | Avis et favoris | Avis sans commande, note, favori | Réputation, confiance |
| PC11 | Profil et adresses | Adresse vide à l'inscription, suppression d'adresse | Livraison correcte |
| PC12 | Recommander | Reconstitution du panier depuis une commande | Fidélisation |

## 5. Approche d'analyse du risque

Chaque risque de `risk-matrix.md` reçoit une **probabilité (1 à 5)** et un **impact (1 à 5)** ; **score = probabilité × impact**.

| Score | Priorité | Effort de test attendu |
|---|---|---|
| 20 à 25 | P0 – Critique | Nominal, limites et erreurs, UI et API, revalidation obligatoire |
| 12 à 19 | P1 – Élevée | Nominal, limites, erreurs |
| 6 à 11 | P2 – Moyenne | Tests ciblés (limite et erreur) |
| 1 à 5 | P3 – Faible | Test de fumée ou exploratoire |

Les probabilités s'appuient sur les indices relevés dans le code (commentaires, absence de contrôles). Elles sont **révisées après exécution** pour refléter les anomalies confirmées.

## 6. Types de tests

| Type | Objectif | Application |
|---|---|---|
| Fumée | Valider que l'application est testable | `/health`, accueil, login, Swagger |
| Fonctionnel nominal | Parcours conforme aux règles | PC1 à PC12 |
| Valeurs limites | Bornes de quantité, minimum, plafond, expiration, stock | Quantité 0, 1, 20, 21 ; sous-total égal au minimum ; stock 0 et stock + 1 |
| Erreur / négatif | Entrées invalides, droits manquants | Clé API absente ou fausse, ID inexistant, JSON invalide, statut invalide |
| Règles métier | Application correcte des règles | Coupon, minimum, restaurant fermé, mono-restaurant, annulation, transitions de statut |
| API (contrat, statuts HTTP) | Codes, schémas JSON, cohérence avec `openapi.yaml` | Swagger, curl |
| Sécurité de base | Authn / authz, CSRF, redirection, usurpation | Accès croisé aux commandes, `next`, formulaire POST depuis une autre origine |
| Exploratoire (charters) | Découvrir ce que les cas écrits ne couvrent pas | Sessions de 30 min par domaine |
| Régression | Revalider les correctifs | Rejeu des cas Fail après correctif en branche séparée |
| Tests utilisateurs | Retours réels | 3 scénarios par au moins 2 personnes |
| Tests automatisés existants | Filet de base | `pytest -q` (dossier `tests/`), exécuté en entrée de campagne |

## 7. Environnement de test

| Élément | Valeur |
|---|---|
| Application | Flask local, `http://127.0.0.1:5000` |
| Swagger UI | `http://127.0.0.1:5000/docs/` |
| Spécification | `http://127.0.0.1:5000/openapi.yaml` |
| Base de données | SQLite (`quickorder.db`), initialisée par `python seed.py` |
| Démarrage | `python run.py`, ou `docker compose up --build` |
| Clé API | En-tête `X-API-Key: quickorder-demo-key` |
| Client | `alice@example.com` / `Password123!` |
| Second client (accès croisé) | `bob@example.com` / `Password123!` |
| Administrateur | `admin@quickorder.local` / `Admin123!` |

Remarques :

- Ces identifiants sont des données de démonstration publiques du projet ; aucune donnée personnelle réelle ne doit être saisie.
- Les tests modifient la base (commandes, stock) : noter l'état initial, restaurer par `seed.py` ou `docker compose down -v` entre deux cycles.
- Dans le code lu, l'API utilise le compte `alice@example.com` quand aucune session web n'est ouverte (voir R13) : les commandes créées via Swagger apparaîtront donc chez Alice.

## 8. Outils

| Outil | Usage |
|---|---|
| Navigateur + DevTools via agent-browser | Parcours UI ; onglets Network, Console, Application (cookie de session) ; captures et traces |
| curl | Requêtes API reproductibles, en-têtes personnalisés, tests négatifs (sans clé, clé erronée, JSON malformé) |
| Swagger UI (`/docs/`) | Exploration et exécution des endpoints via **Authorize** |
| Postman / Bruno (optionnel) | Collection `docs/quickorder-api.postman_collection.json` |
| pytest | Tests automatisés de base fournis |
| Tableur (`test-cases.xlsx`) | Cas de test et suivi des statuts |
| Git | Traçabilité : bug reports dans `docs/bug-reports/`, preuves dans `docs/evidence/` |

Preuves attendues : capture ou vidéo pour l'UI, requête et réponse complètes (statut, corps) pour l'API, extrait de console ou du réseau si pertinent. Chaque preuve est nommée avec l'ID du cas ou du bug.

## 9. Critères d'entrée

- Application démarrée, `/health` renvoie `status: ok`.
- Base initialisée par `seed.py`, comptes de démonstration opérationnels.
- Swagger accessible, clé API fonctionnelle.
- Documents de référence lus (`STUDENT_BRIEF.md`, `README.md`, `API.md`).
- Matrice de risques validée par l'équipe, cas de test relus.
- `pytest -q` exécuté et résultat consigné (état de référence).

## 10. Critères de sortie

- 100 % des cas P0 exécutés, au moins 90 % des cas P1, au moins 70 % des cas P2.
- Au moins 24 cas rédigés (6 nominaux, 6 limites, 6 erreurs, 6 règles métier), chacun avec un statut (Pass, Fail, Blocked, Skipped) justifié.
- Au moins 8 bug reports reproductibles avec preuve, sévérité et priorité.
- Rapport d'exécution : nombre de tests, Pass, Fail, Blocked, Skipped, principaux risques, recommandation Go / No-Go.
- Tests utilisateurs réalisés (3 scénarios, 2 personnes minimum) et plan d'amélioration (au moins 6 actions).
- Chaque Blocked a une cause et un plan de déblocage.

## 11. Critères Go / No-Go

La recommandation est formulée à partir de l'état **constaté** à la fin de la campagne.

| Décision | Conditions |
|---|---|
| **No-Go** | Au moins un défaut ouvert de sévérité Critique (perte financière, doublon de commande, contournement d'authentification ou d'autorisation, perte ou corruption de données), **ou** au moins 3 défauts Majeurs ouverts sur un parcours critique (PC1 à PC8) |
| **Go conditionnel** | Aucun Critique ouvert ; Majeurs ouverts avec contournement documenté et correctif planifié ; plus de 90 % des cas P0 et P1 en Pass |
| **Go** | Aucun Critique ni Majeur ouvert ; défauts Mineurs consignés au backlog ; critères de sortie atteints |

| Sévérité | Définition |
|---|---|
| Critique | Perte financière ou de données, faille de sécurité exploitable, parcours critique inutilisable |
| Majeure | Règle métier clé non respectée, contournement difficile ou inexistant |
| Mineure | Écart fonctionnel limité, contournement simple |
| Cosmétique | Libellé ou affichage, sans effet fonctionnel |

La priorité de correction (P0 à P3) est distincte de la sévérité : elle intègre la fréquence et l'urgence métier.

## 12. Priorisation risque × impact

Le détail figure dans `risk-matrix.md`. Ordre d'exécution proposé :

1. **Vague 1 (P0)** : paiement et totaux (PC1 à PC3), stock (PC4), restaurant fermé et minimum (PC5), API commandes et authentification (PC6, PC8).
2. **Vague 2 (P1)** : annulation et statuts (PC7), avis (PC10), recherche et filtres (PC9), adresses (PC11).
3. **Vague 3 (P2, P3)** : recommander, favoris, profil, finitions, exploratoire libre.

Le temps restant est reporté en exploratoire sur les zones où des défauts ont été confirmés (regroupement des défauts).

## 13. Indices relevés dans le code (hypothèses à confirmer)

Les commentaires `INTENTIONAL QA BUG` et l'absence de certains contrôles dans `app/` orientent la conception des cas. Chaque point doit être **reproduit** avant d'être déclaré bug.

| Zone | Indice observé dans le code | Test à concevoir |
|---|---|---|
| Panier web | Commentaires indiquant que stock 0 et quantité supérieure au stock ne sont pas bloqués ; aucune borne maximale sur la quantité | Ajouter un produit à stock 0 ; saisir une quantité très élevée |
| Checkout | `is_open`, `minimum_order`, stock et disponibilité ne sont pas revérifiés au POST final | Commander chez un restaurant fermé ; sous le minimum |
| Cash | Le montant reçu est utilisé pour calculer la monnaie sans comparaison au total | `cash_received` = 1 |
| PayPal | Le code crée une seconde commande identique (web et API) | Compter les commandes avant et après |
| API | Clé comparée à un en-tête ; utilisateur Alice si pas de session ; validation de coupon sur le sous-total fourni ; liste incluant les restaurants fermés | Appels sans clé, avec clé fausse, avec sous-total modifié |
| Admin | Aucun contrôle de cohérence des transitions de statut | `delivered` vers `confirmed` |
| Avis | Aucun lien exigé avec une commande ; pas de recalcul de la note du restaurant dans le code lu | Avis sans commande ; observer `rating` |
| Auth | Aucune occurrence « csrf » dans `app/` ; redirection vers `next` sans validation ; déconnexion en GET | Formulaire d'une autre origine ; `?next=` externe ; lien de déconnexion |
| Filtres | Le filtre de frais de livraison utilise `>=` ; la recherche ne porte que sur le nom | `max_delivery=2.5` ; recherche par mot de la description |
| Coupon | Commentaire signalant un écart entre le taux annoncé et le taux stocké d'une promotion | Comparer le texte promo et la réduction réelle |

## 14. Rôles et livrables

| Rôle | Responsabilité |
|---|---|
| Responsable QA | Stratégie, matrice de risques, arbitrage Go / No-Go |
| Testeurs UI | Cas web, DevTools, preuves |
| Testeurs API | Cas Swagger / curl, contrat |
| Rédacteur bugs | Qualité et reproductibilité des rapports |
| Animateur tests utilisateurs | Scénarios, verbatims, synthèse |

Livrables : `test-strategy.md`, `risk-matrix.md`, `test-cases.xlsx`, `execution-report.md`, `bug-reports/`, `user-feedback.md`, `improvement-plan.md`.

## 15. Gestion des changements et limites

- `app/` n'est pas modifié pendant la campagne initiale ; toute correction est proposée en branche séparée puis revalidée par rejeu des cas Fail.
- Limites : environnement local mono-utilisateur, SQLite, paiement simulé, un seul navigateur. Les résultats ne se généralisent pas à une charge réelle ni à un fournisseur de paiement réel.
- Les scores de risque sont des jugements d'équipe, révisables à chaque cycle.
