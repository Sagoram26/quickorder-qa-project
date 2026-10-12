# Rapport de revalidation - branche `fix/qa-corrections`

Application corrigée lancée sur le port 5001 (DB SQLite temporaire, seed rejoué), campagne `docs/revalidation/_campaign_script.py` (copie du script de master, BASE = 5001). Preuves JSON : `docs/revalidation/TC-*.json`.
Pytest : `21 passed` (6 tests initiaux + 15 tests de non-régression dans `tests/test_regression_qa.py`).

## Comptes avant / après (36 cas)

| | Pass | Fail |
|---|---|---|
| Avant (master) | 20 | 16 |
| Après (fix/qa-corrections) | 35 | 1 |

## Bug -> statut -> cas rejoué -> résultat réel

| Bug | Statut | Cas TC | Résultat |
|---|---|---|---|
| BUG-001 stock 0 ajoutable | Corrigé (ajout refusé, bouton grisé) | TC-ERR-04 | Pass |
| BUG-002 stock négatif | Corrigé (quantité plafonnée au stock, revalidation checkout UI/API) | TC-LIM-06 | Pass (stock final 0, jamais négatif) |
| BUG-003 restaurant fermé | Corrigé (panier, checkout, API POST /orders -> 409) | TC-REG-02 | Pass |
| BUG-004 minimum de commande | Corrigé UI + API | TC-REG-03 | Pass |
| BUG-005 espèces insuffisantes | Corrigé UI + API | TC-ERR-06 | Pass |
| BUG-006 doublon PayPal | Corrigé UI + API | TC-REG-05 | Pass |
| BUG-007 ATLAS15 | Corrigé (seed.py, 15 %) | TC-REG-04 | Pass |
| BUG-008 filtre max_delivery | Corrigé (`<=`) | TC-LIM-05 | Pass |
| BUG-009 transitions admin | Corrigé (matrice, delivered/cancelled finaux) | TC-REG-06 | Pass |
| BUG-010 avis sans commande | Corrigé (commande livrée requise) | TC-REG-07 | Pass |
| BUG-011 open redirect | Corrigé (`next` relatif interne seulement) | TC-ERR-10 | Pass |
| BUG-012 API sans session | Corrigé (401 sans session, plus de repli alice) | TC-ERR-09 | Pass |
| BUG-013 coupon invalide API | Non corrigé (hors périmètre demandé) | TC-ERR-07 | Fail |
| BUG-014 recherche description | Corrigé UI + API | TC-LIM-08 | Pass |
| BUG-015 adresse vide | Corrigé (plus d'adresse à l'inscription, adresse complète exigée) | TC-ERR-12 | Pass |
| BUG-016 logout GET | Corrigé (POST, bouton formulaire, cookie SameSite=Lax) | TC-ERR-13 | Pass |

## Réserves et choix

- Pas de jeton CSRF (pas de Flask-WTF) : le logout POST + SameSite=Lax réduit le risque mais ne le supprime pas.
- Le restaurant fermé reste listé dans `GET /api/restaurants` (is_open exposé) ; seules les commandes sont refusées.
- Ajustements du script rejoué (copie uniquement) : appels `POST /api/orders` faits avec une session Alice (l'API exige désormais une session) ; TC-LIM-06 accepte "quantité plafonnée" (attendu BUG-002 : plafond OU refus, stock jamais négatif) ; TC-ERR-06/12/09 tolèrent l'absence de commande/adresse/items.
- TC-ERR-13 : le critère du script ("pas de déconnexion par GET") est faible ; la vérification réelle est `test_bug016_logout_is_post_only` (GET /logout -> 405).
- Modification d'un test existant : `test_restaurants_api_requires_key` attend 2 restaurants (le fixture contient désormais un restaurant fermé).
- Comportement API : `/api/orders*` et `/api/favorites` exigent clé + session login.
