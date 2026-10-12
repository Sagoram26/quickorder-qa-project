# BUG-013 — L'API POST /api/orders ignore silencieusement un coupon invalide et crée la commande

- **ID** : BUG-013
- **Cas de test lié** : TC-ERR-07
- **Sévérité** : Mineure
- **Priorité** : P3

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Clé API de démo ; produit #1 (Classic Burger, 11.90 €) disponible ; session ou repli d'API valide.

## Étapes de reproduction

1. Exécuter : `curl -i -X POST http://127.0.0.1:5000/api/orders -H "X-API-Key: quickorder-demo-key" -H "Content-Type: application/json" -d '{"items":[{"product_id":1,"quantity":2}],"coupon":"CODEINVALIDE"}'`.
2. Observer le statut HTTP et le champ `discount` de la réponse.
3. Comparer avec `POST /api/coupons/validate` (même coupon) qui signale l'invalidité.

## Résultat attendu

HTTP 400/422 avec un message d'erreur « Coupon invalide », et aucune commande créée.

## Résultat obtenu

HTTP 201, commande #6 créée : `discount: 0.0`, `subtotal: 23.8`, `delivery_fee: 2.99`, `total: 26.79`, `status: confirmed`, `payment_status: paid`. Aucune erreur signalée au client.

## Preuve

- `docs/evidence/screenshots/BUG-013.png`
- `docs/evidence/TC-ERR-07.json`

## Impact

Le client ne sait pas que son code est refusé ; incohérence avec `/api/coupons/validate` ; erreurs de facturation non détectées côté intégrateur.

## Piste de cause (lecture seule, `app/`)

`app/routes/api.py:165-171` : `if coupon and subtotal >= coupon.min_order_amount:` sans branche `else` renvoyant une erreur quand `code` est non vide mais inconnu/inactif/minimum non atteint.
