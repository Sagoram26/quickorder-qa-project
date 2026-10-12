# Plan d'amélioration - QuickOrder

Base : 36 cas exécutés (20 Pass, 16 Fail), 16 bugs (BUG-001 à BUG-016, dont 4 critiques : 003, 005, 006, 012). Les retours utilisateurs (`user-feedback.md`) sont simulés ; les priorités reposent surtout sur les bugs prouvés.

Échelle : impact et effort en Faible / Moyen / Élevé. MoSCoW : Must / Should / Could.

## Tableau récapitulatif

| # | Amélioration | MoSCoW | Impact | Effort | Bugs liés | Vague |
|---|--------------|--------|--------|--------|-----------|-------|
| 1 | Authentification API par utilisateur (supprimer le repli alice) | Must | Élevé | Faible | BUG-012 | 1 |
| 2 | Validation serveur du checkout (ouvert, minimum, espèces, adresse) y compris API | Must | Élevé | Moyen | BUG-003, 004, 005, 015 | 1 |
| 3 | Transaction atomique + contrôle de stock au checkout | Must | Élevé | Moyen | BUG-001, 002 | 1 |
| 4 | Suppression du doublon PayPal (commande idempotente) | Must | Élevé | Faible | BUG-006 | 1 |
| 5 | Cohérence promo (ATLAS15) et erreurs de coupon explicites | Must | Moyen | Faible | BUG-007, 013 | 1 |
| 6 | Protection CSRF, logout en POST, validation de `next` | Must | Moyen | Moyen | BUG-011, 016 | 1 |
| 7 | Machine d'états des commandes | Should | Moyen | Moyen | BUG-009 | 2 |
| 8 | Tests automatisés de non-régression (pytest), un par bug | Must | Élevé | Moyen | BUG-001 à 016 | 1 (socle) puis 2 |
| 9 | Correction filtre livraison et recherche (nom + description) | Should | Moyen | Faible | BUG-008, 014 | 2 |
| 10 | Avis réservés aux clients ayant commandé | Could | Faible | Faible | BUG-010 | 3 |
| 11 | Retours d'erreur UX clairs (restaurant fermé grisé, stock épuisé affiché) | Could | Moyen | Moyen | BUG-001, 003 | 3 |

## Détail

### 1. Authentification API par utilisateur (Must)
- **Justification** : sans session, l'API agit comme alice : fuite et modification de données d'autrui. C'est le risque n°1.
- **Critère d'acceptation** : tout appel API sans session valide renvoie 401 ; avec la session de bob, aucune donnée d'alice n'est lisible (403/404). Test pytest sans cookie : 401.

### 2. Validation serveur du checkout (Must)
- **Justification** : les contrôles ne doivent pas dépendre de l'interface ; la même fonction doit servir le web et l'API.
- **Critère d'acceptation** : commande refusée (400/422, message clair, aucune commande créée) si restaurant fermé, sous-total < minimum, espèces < total, ou adresse vide ; acceptée aux bornes exactes (espèces = total, sous-total = minimum).

### 3. Transaction atomique + stock (Must)
- **Justification** : l'ajout et le décrément doivent se faire en une transaction avec contrainte `stock >= 0`, sinon survente.
- **Critère d'acceptation** : ajout d'un plat à stock 0 refusé ; deux commandes concurrentes sur le dernier article : une réussit, l'autre échoue ; le stock n'est jamais négatif ; échec = rollback complet (pas de commande partielle).

### 4. Suppression du doublon PayPal (Must)
- **Justification** : double facturation, perte de confiance directe.
- **Critère d'acceptation** : un paiement PayPal crée exactement une commande (comptage en base) ; rejouer la même requête avec la même clé d'idempotence ne crée rien de plus.

### 5. Cohérence promo et coupons (Must)
- **Justification** : annonce 15 %, application 10 % : risque de litige et de non-conformité. Un coupon invalide ignoré en silence trompe l'utilisateur.
- **Critère d'acceptation** : ATLAS15 sur 100 € donne 15 € de remise (plafond éventuel documenté et affiché) ; un taux unique défini en base et utilisé par l'affichage et le calcul ; coupon invalide via API renvoie 400 avec message.

### 6. CSRF, logout POST, `next` (Must)
- **Justification** : un lien externe peut déconnecter l'utilisateur ; le `next` non validé permet du phishing.
- **Critère d'acceptation** : GET /logout renvoie 405 ; POST sans jeton CSRF renvoie 403 ; `next=https://evil.example` redirige vers l'accueil, seuls les chemins relatifs internes sont acceptés.

### 7. Machine d'états des commandes (Should)
- **Justification** : l'admin peut faire revenir une commande en arrière (annulée vers en préparation).
- **Critère d'acceptation** : seules les transitions pending -> confirmed -> preparing -> delivered et annulation avant livraison sont acceptées ; cancelled et delivered sont terminaux ; toute autre transition renvoie 409, testée pour chaque paire interdite.

### 8. Tests de non-régression pytest (Must)
- **Justification** : chaque bug corrigé doit rester corrigé ; les 16 échecs sont déjà décrits avec preuves.
- **Critère d'acceptation** : au moins un test pytest par BUG-001 à 016, rouge avant correctif et vert après ; exécution automatique dans la CI à chaque commit ; build bloqué si un test échoue.

### 9. Filtre livraison et recherche (Should)
- **Justification** : bug perçu par 2/2 personas ; résultat inversé donc trompeur.
- **Critère d'acceptation** : « livraison gratuite » ne retourne que des restaurants à frais 0 ; la recherche d'un mot présent uniquement dans la description retourne le restaurant.

### 10. Avis après commande (Could)
- **Justification** : intégrité des notes, faible risque.
- **Critère d'acceptation** : avis sans commande livrée de l'utilisateur chez ce restaurant renvoie 403 ; avec commande, 201.

### 11. UX d'erreur (Could)
- **Justification** : une fois les contrôles serveur en place, l'utilisateur doit comprendre pourquoi (verbatims A3, C1).
- **Critère d'acceptation** : restaurant fermé : bouton de commande désactivé avec mention « fermé » ; plat épuisé : badge « épuisé » et bouton désactivé ; tests E2E sur ces deux cas.

## Feuille de route

| Vague | Contenu | Condition de sortie |
|-------|---------|---------------------|
| **1 - Avant mise en production** (bloquant) | #1, #2, #3, #4, #5, #6, socle de #8 (tests des bugs critiques et élevés) | Les 4 bugs critiques (003, 005, 006, 012) corrigés ; tests verts en CI ; nouvelle exécution des 36 cas sans échec bloquant |
| **2 - Sprint suivant** | #7, #9, complétion de #8 (BUG-001 à 016 tous couverts) | 100 % des bugs couverts par un test ; aucun Fail restant sur les 36 cas |
| **3 - Plus tard** | #10, #11, tests utilisateurs réels pour remplacer les retours simulés | Retours réels recueillis, priorités revues |
