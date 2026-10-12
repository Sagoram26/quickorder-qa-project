# BUG-006 — Un paiement PayPal crée deux commandes

- **ID** : BUG-006
- **Cas de test lié** : TC-REG-05
- **Sévérité** : Critique — **Priorité** : P1

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`).
- Compte client : alice@example.com / Password123! (adresse id 1 existante).
- Noter le nombre de commandes existantes via `GET /api/orders` (n0).

## Étapes
1. Se connecter en tant qu'Alice ; `curl -b cj.txt -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/orders` (n0).
2. `POST /cart/add/1` avec `quantity=2` (Classic Burger).
3. `POST /checkout` avec `confirm=1, address_id=1, payment_method=paypal, coupon=, customer_note=QA`.
4. Relire `GET /api/orders`.

## Résultat attendu
Une seule commande créée (n0 + 1).

## Résultat obtenu
Deux commandes créées (n0 + 2) : #10 et #11, chacune « Classic Burger × 2 », total 26.79, paiement paypal / paid. L'UI redirige vers `/orders/10`.

## Preuve
- `docs/evidence/screenshots/BUG-006.png`
- `docs/evidence/TC-REG-05.json`
- `docs/evidence/_campaign_script.py` (l. 216-219)

## Impact
Double facturation et double préparation ; stock décrémenté deux fois.

## Piste de cause (lecture seule)
- `app/routes/orders.py:118-124` : bloc `if payment == "paypal"` qui rappelle `build_order` et `add_order_items`.
- `app/routes/api.py:199-210` : même duplication côté API (non exécutée dans la campagne).
