# BUG-002 — Quantité supérieure au stock acceptée au checkout, stock négatif

- **ID** : BUG-002
- **Cas de test lié** : TC-LIM-06
- **Sévérité** : Majeure — **Priorité** : P2

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`).
- Compte client : alice@example.com / Password123! (adresse id 1 existante).
- Seed : « Salmon Bowl » (id 7, Tokyo Bowl, 15,90 €) a un stock de 2 (`seed.py:19`).

## Étapes
1. `curl -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/products/7` → `stock: 2`.
2. Se connecter en tant qu'Alice.
3. `POST /cart/add/7` avec `quantity=3` (UI : ajouter 3 Salmon Bowl).
4. `POST /checkout` avec `confirm=1, address_id=1, payment_method=card, coupon=, customer_note=QA`.
5. Relire `curl -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/products/7`.

Variante API (même défaut dans le code, non exécutée dans la campagne) : `curl -X POST http://127.0.0.1:5000/api/orders -H "X-API-Key: quickorder-demo-key" -H "Content-Type: application/json" -b cj.txt -d '{"items":[{"product_id":7,"quantity":3}],"payment_method":"card"}'` (session Alice dans `cj.txt`).

## Résultat attendu
Quantité limitée au stock (2) ou checkout refusé ; stock jamais négatif.

## Résultat obtenu
- Ajout de 3 unités accepté (HTTP 200, « Salmon Bowl ajouté au panier. »).
- Commande #4 confirmée : « Salmon Bowl × 3 47.70 € », total 51.19 €, paiement paid · card.
- Stock après commande : -1 (avant : 2).

## Preuve
- `docs/evidence/screenshots/BUG-002.png`
- `docs/evidence/TC-LIM-06.json`
- `docs/evidence/_campaign_script.py` (l. 144-147)

## Impact
Survente et stock incohérent (négatif) ; commandes non honorables.

## Piste de cause (lecture seule)
- `app/routes/shop.py:38-39` (mise à jour du panier) et `app/cart.py:14, 21` : quantité non plafonnée par le stock.
- `app/routes/orders.py:68-69` (`add_order_items`) : `product.stock -= item["quantity"]` sans contrôle ; stock non revalidé avant paiement (`orders.py:104-107`).
- `app/routes/api.py:159-160` (stock ignoré) et `api.py:198` : même défaut côté API.
