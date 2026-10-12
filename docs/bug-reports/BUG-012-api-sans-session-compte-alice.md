# BUG-012 — L'API avec clé seule (sans session) retombe sur le compte d'Alice et expose ses commandes ; le test pytest existant plante en AttributeError

- **ID** : BUG-012
- **Cas de test lié** : TC-ERR-09
- **Sévérité** : Critique (sécurité)
- **Priorité** : P1

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Application lancée, aucune session ouverte (aucun cookie). Clé API de démo `quickorder-demo-key`. Le compte alice@example.com existe (cas 1) ou non (cas 2, pytest).

## Étapes de reproduction

1. Exécuter : `curl -i -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/orders` (sans cookie de session).
2. Constater le contenu retourné : les commandes d'Alice.
3. Variante (alice absente) : exécuter `.venv\Scripts\python.exe -m pytest -q` dans le dossier du projet.

## Résultat attendu

Sans session utilisateur, `/api/orders` doit répondre HTTP 401 (utilisateur non authentifié), et ne jamais retourner de données d'un compte tiers. Le test de fumée doit réussir ou échouer proprement, sans exception.

## Résultat obtenu

Cas 1 : HTTP 200, `"count": 6`, 6 commandes d'Alice (ids 6, 5, 4, …) retournées à un appelant anonyme. Cas 2 (pytest) : `1 failed, 5 passed in 1.52s` ; `FAILED tests/test_smoke.py::test_api_orders_with_key - AttributeError: 'NoneType' object has no attribute 'id'` à `app\routes\api.py:219` (`query = Order.query.filter_by(user_id=api_customer().id)`).

## Preuve

- `docs/evidence/screenshots/BUG-012.png`
- `docs/evidence/TC-ERR-09.json`
- `docs/evidence/_results.json`
- `sortie réelle de `.venv\Scripts\python.exe -m pytest -q` (1 failed, 5 passed)`

## Impact

Fuite de données personnelles/commandes entre comptes (contrôle d'accès cassé, OWASP A01) ; toute personne connaissant la clé de démo lit les données d'Alice et, via POST /api/orders, peut créer des commandes à son nom (la commande #6 de la campagne l'a été ainsi). Crash 500 si le compte d'Alice n'existe pas.

## Piste de cause (lecture seule, `app/`)

`app/routes/api.py:27-31` (`api_customer`) : si `current_user` n'est pas authentifié, repli codé en dur sur `User.query.filter_by(email="alice@example.com").first()` (l.30), qui peut renvoyer `None`. Utilisé sans contrôle en `api.py:219` (`list_orders`). Le test `tests/test_smoke.py::test_api_orders_with_key` échoue pour cette raison quand alice est absente.
