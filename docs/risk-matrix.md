# Matrice de risques — QuickOrder V3.1

Document lié : `test-strategy.md` (sections 5 et 12).

## 1. Lecture et limites

- Chaque risque est parti d'une hypothèse issue de la lecture du code (`app/`). Il n'est dit **confirmé** que si un test exécuté a produit une preuve (`docs/evidence/`).
- **Score = probabilité (1 à 5) × impact (1 à 5)**. Probabilité : 1 improbable, 5 quasi certain (indice explicite dans le code ou contrôle absent). Impact : 1 négligeable, 5 perte financière, atteinte à la sécurité ou parcours critique bloqué.
- **Priorité** : P0 (20 à 25), P1 (12 à 19), P2 (6 à 11), P3 (1 à 5).
- Les identifiants de tests liés (`TC-xxx`) sont ceux de `test-cases.xlsx` (36 cas exécutés: 20 Pass, 16 Fail). « Non exécuté » signale un risque non couvert par la campagne initiale.
- Mise à jour après la campagne: probabilité portée à 5 pour un risque confirmé, réduite pour un risque infirmé; colonne « Statut » : Confirmé via BUG-xxx, Infirmé, À vérifier.

## 2. Tableau des risques

| ID | Risque (hypothèse à vérifier) | Indice dans le code | Proba | Impact | Score | Priorité | Parcours | Tests liés | Statut |
|---|---|---|:-:|:-:|:-:|:-:|---|---|---|
| R01 | Une commande `cash` pourrait être acceptée avec un montant reçu inférieur au total (monnaie négative) ou absent, sur le web et l'API | `build_order` et `create_order_api` calculent `change_due` sans comparer au total ; commentaire dédié | 5 | 5 | 25 | P0 | PC2 | TC-ERR-06 | Confirmé via BUG-005 |
| R02 | Le paiement PayPal pourrait créer deux commandes identiques (double facturation, double décrément de stock), sur le web et l'API | Second `build_order` / second `Order` dans le bloc `paypal` ; commentaire dédié | 5 | 5 | 25 | P0 | PC2 | TC-REG-05 | Confirmé via BUG-006 |
| R03 | Un restaurant fermé pourrait recevoir des commandes (ajout au panier, checkout, API) | Pas de contrôle de `is_open` dans `add`, `checkout`, `create_order_api` | 5 | 4 | 20 | P0 | PC5 | TC-REG-02 | Confirmé via BUG-003 |
| R04 | Le minimum de commande du restaurant pourrait être affiché mais non appliqué (web et API) | Aucun usage de `minimum_order` dans la validation de checkout ni de l'API | 5 | 3 | 15 | P1 | PC5 | TC-REG-03 | Confirmé via BUG-004 |
| R05 | Le stock pourrait ne pas être contrôlé lors de la commande : quantité supérieure au stock acceptée, stock négatif après décrément | `product.stock -= quantity` sans test ; panier sans borne de stock ; API sans test de stock | 5 | 4 | 20 | P0 | PC4 | TC-LIM-06 | Confirmé via BUG-002 |
| R06 | Un produit à stock 0 pourrait rester visible, ajoutable au panier et commandable | Requête de page restaurant filtrée sur `available` seulement ; commentaire dédié | 5 | 3 | 15 | P1 | PC4 | TC-ERR-04 | Confirmé via BUG-001 |
| R07 | La disponibilité d'un produit déjà au panier pourrait ne pas être revérifiée au checkout (produit devenu indisponible ou supprimé) | `cart_items` ignore la disponibilité ; checkout ne la contrôle pas | 4 | 3 | 12 | P1 | PC4 | Non exécuté | À vérifier (hors campagne initiale) |
| R08 | Le calcul des coupons pourrait être incohérent : taux réel différent du taux annoncé (promotion ATLAS), arrondi, plafond, expiration ou minimum mal bornés ; coupon invalide ignoré silencieusement par l'API de commande | Commentaire sur le coupon ATLAS ; `create_order_api` ne signale pas un coupon refusé | 5 | 3 | 15 | P1 | PC3 | TC-REG-04, TC-REG-08, TC-LIM-01, TC-LIM-02, TC-LIM-03, TC-ERR-03, TC-ERR-07 | Confirmé via BUG-007 et BUG-013 (bornes et expiration conformes: Pass) |
| R09 | `POST /api/coupons/validate` pourrait faire confiance au `subtotal` fourni par le client (réduction calculée sur une valeur arbitraire) ; coupon réutilisable sans limite | Sous-total lu dans le JSON ; aucun suivi d'usage de coupon dans `models.py` | 4 | 3 | 12 | P1 | PC3 | Non exécuté (TC-LIM-01 à 03 envoient le subtotal côté client, sans le comparer à un panier) | À vérifier (hors campagne initiale) |
| R10 | L'admin pourrait appliquer des transitions de statut incohérentes (`delivered` vers `confirmed`, `delivered` vers `cancelled`) | Aucune machine d'états dans `update_order_status` ; commentaire dédié | 5 | 3 | 15 | P1 | PC7 | TC-REG-06 | Confirmé via BUG-009 |
| R11 | L'annulation pourrait laisser le stock et le statut de paiement inchangés (pas de remise en stock, `payment_status` reste « paid ») ; règles d'annulation web et API à comparer | `cancel_order` et l'annulation web changent seulement `status` | 3 | 3 | 9 | P2 | PC7 | Non exécuté (annulation nominale: TC-NOM-07 Pass) | À vérifier (stock et paiement après annulation non contrôlés) |
| R12 | Absence de protection CSRF : un site tiers pourrait déclencher des actions authentifiées (ajout, annulation, avis, favori) ; déconnexion possible par simple GET | Aucune occurrence « csrf » dans `app/` ; `logout` en GET ; formulaires POST sans jeton | 4 | 4 | 16 | P1 | PC8 | TC-ERR-13 | Confirmé en partie via BUG-016 (logout GET); absence de jeton CSRF sur les formulaires non exploitée |
| R13 | Redirection ouverte après connexion via `?next=` (URL externe) | `redirect(request.args.get("next") ...)` sans validation | 5 | 3 | 15 | P1 | PC8 | TC-ERR-10 | Confirmé via BUG-011 |
| R14 | Authentification API faible : clé unique, statique et publique ; clé et `SECRET_KEY` de session ayant des valeurs par défaut en configuration | `API_KEY` et `SECRET_KEY` avec valeurs par défaut dans `config.py` ; comparaison à une constante | 3 | 4 | 12 | P1 | PC6 | TC-ERR-01 | Partiellement infirmé: clé obligatoire (401 sans clé, Pass); clé statique par défaut non évaluée |
| R15 | Sans session web, l'API agirait au nom d'Alice (utilisateur par défaut) : toute personne disposant de la clé pourrait créer, lister et annuler les commandes d'Alice | `api_customer()` retourne `alice@example.com` si non authentifié | 5 | 4 | 20 | P0 | PC6 | TC-ERR-09 | Confirmé via BUG-012 |
| R16 | Validation d'entrée API insuffisante : corps mal formé pouvant produire une erreur 500 (élément non objet dans `items`, `product_id` non hashable), `cash_received` invalide converti en 0, plafond de quantité API (20) absent côté web | Accès `item.get` hors garde, conversions silencieuses | 2 | 3 | 6 | P2 | PC6 | TC-LIM-04, TC-ERR-05 | Partiellement infirmé: bornes de quantité et items vides rejetés (Pass); JSON mal typé non testé |
| R17 | Le filtre « frais de livraison maximum » pourrait être inversé (renvoie les frais supérieurs ou égaux) | `Restaurant.delivery_fee >= max_delivery` | 5 | 3 | 15 | P1 | PC9 | TC-LIM-05 | Confirmé via BUG-008 |
| R18 | Recherche limitée au nom (UI et API) ; l'API liste aussi les restaurants fermés alors que l'UI parle de restaurants commandables ; tri et filtre végétarien à contrôler | `ilike` sur `name` uniquement ; pas de filtre `is_open` dans `/api/restaurants` | 5 | 2 | 10 | P2 | PC9 | TC-LIM-08, TC-NOM-03, TC-REG-02 | Confirmé via BUG-014 (description) et BUG-003 (API liste restaurant fermé) |
| R19 | Un avis pourrait être déposé sans avoir commandé et sans limite de nombre ; la note affichée du restaurant pourrait ne pas évoluer | Commentaire dédié ; aucun recalcul de `Restaurant.rating` dans `review` | 5 | 2 | 10 | P2 | PC10 | TC-REG-07 | Confirmé via BUG-010 |
| R20 | Adresses : un compte inscrit possède une adresse vide par défaut utilisable au checkout ; adresse « 10 rue de Paris » créée automatiquement ; suppression d'une adresse liée à une commande à contrôler | `register` crée une adresse vide ; `checkout` crée une adresse par défaut | 5 | 3 | 15 | P1 | PC11 | TC-ERR-12 | Confirmé via BUG-015 |
| R21 | Contrôle d'accès aux commandes : accès croisé client à client, accès admin, recommander par un admin ; incohérences UI / API (redirection vs 403) | Tests `user_id` dans le web et l'API ; `reorder` sans exception admin | 1 | 5 | 5 | P3 | PC7, PC8 | TC-ERR-08, TC-ERR-11 | Infirmé: accès croisé refusé (UI: message, API: 403) et /admin/ protégé (Pass) |
| R22 | Concurrence sur le stock avec SQLite (deux commandes simultanées, décrément non atomique) | `product.stock -= n` en lecture puis écriture | 2 | 3 | 6 | P2 | PC4 | Non exécuté | À vérifier (hors campagne initiale) |
| R23 | « Recommander » pourrait ignorer des lignes ou plafonner silencieusement la quantité | `reorder` ignore les produits indisponibles et plafonne à `stock` | 2 | 2 | 4 | P3 | PC12 | Non exécuté | À vérifier (hors campagne initiale) |
| R24 | Favoris : bascule instable, doublon, comportement sans connexion | Contrainte d'unicité en base ; route protégée | 2 | 1 | 2 | P3 | PC10 | Non exécuté | À vérifier (hors campagne initiale) |

## 3. Synthèse par priorité (après campagne)

| Priorité | Risques | Nombre |
|---|---|:-:|
| P0 (20 à 25) | R01, R02, R03, R05, R15 | 5 |
| P1 (12 à 19) | R04, R06, R07, R08, R09, R10, R12, R13, R14, R17, R20 | 11 |
| P2 (6 à 11) | R11, R16, R18, R19, R22 | 5 |
| P3 (1 à 5) | R21, R23, R24 | 3 |

## 4. Carte de chaleur (probabilité × impact, après campagne)

| Proba \ Impact | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** |  | R18, R19 | R04, R06, R08, R10, R13, R17, R20 | R03, R05, R15 | R01, R02 |
| **4** |  |  | R07, R09 | R12 |  |
| **3** |  |  | R11 | R14 |  |
| **2** | R24 | R23 | R16, R22 |  |  |
| **1** |  |  |  |  | R21 |

## 5. Couverture des domaines demandés

| Domaine | Risques |
|---|---|
| Panier | R05, R06, R07 |
| Coupons | R08, R09 |
| Checkout et paiement (card, paypal, cash) | R01, R02, R04 |
| Stock | R05, R06, R07, R22 |
| Restaurant fermé | R03, R18 |
| Annulation et statuts admin | R10, R11, R21 |
| Avis | R19 |
| Authentification, session, CSRF, redirection | R12, R13, R14, R21 |
| API (clé, commandes, utilisateur par défaut) | R01, R02, R03, R09, R14, R15, R16 |
| Filtres et recherche | R17, R18 |
| Adresses, recommander, favoris | R20, R23, R24 |

## 6. Utilisation dans la campagne

1. Écrire d'abord les cas des risques P0, puis P1 (voir ordre des vagues dans `test-strategy.md`).
2. Pour chaque cas Fail, ouvrir un bug dans `docs/bug-reports/` et reporter son identifiant dans la colonne « Statut ».
3. Réviser probabilité et score après exécution : un risque infirmé tombe en P3, un risque confirmé voit sa probabilité portée à 5.
4. Réexécuter les cas liés aux risques P0 et P1 après chaque correctif (revalidation).
5. Reprendre les scores confirmés dans l'analyse de campagne et la recommandation Go / No-Go de `execution-report.md`.
