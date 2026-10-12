# BUG-004 — Minimum de commande non appliqué

- **ID** : BUG-004
- **Cas de test lié** : TC-REG-03
- **Sévérité** : Majeure — **Priorité** : P2

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`).
- Compte client : alice@example.com / Password123! (adresse id 1 existante).
- Seed : Burger Factory, minimum de commande 20,00 €, livraison 2,99 € ; « Frites maison » (id 3) à 3,50 €.

## Étapes
1. Se connecter en tant qu'Alice.
2. `POST /cart/add/3` avec `quantity=1` (sous-total 3,50 € < 20,00 €).
3. `POST /checkout` avec `confirm=1, address_id=1, payment_method=card, coupon=, customer_note=QA`.
4. Vérifier : `curl -b cj.txt -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/orders/9` (session Alice dans `cj.txt`).

## Résultat attendu
Checkout refusé avec un message indiquant que le minimum de commande de 20,00 € n'est pas atteint.

## Résultat obtenu
Commande #9 confirmée : sous-total 3.5, livraison 2.99, total 6.49, `payment_status` paid, `status` confirmed.

## Preuve
- `docs/evidence/screenshots/BUG-004.png`
- `docs/evidence/TC-REG-03.json`
- `docs/evidence/_campaign_script.py` (l. 209-211)

## Impact
Commandes non rentables ; règle métier affichée mais non respectée (UI et API).

## Piste de cause (lecture seule)
- `app/routes/orders.py:104-106` : `minimum_order` affiché mais jamais appliqué.
- `app/routes/api.py:180-181` : pas de contrôle de minimum côté API.
