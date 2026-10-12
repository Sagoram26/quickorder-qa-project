# BUG-005 — Espèces insuffisantes acceptées, monnaie à rendre négative

- **ID** : BUG-005
- **Cas de test lié** : TC-ERR-06
- **Sévérité** : Critique — **Priorité** : P1

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`).
- Compte client : alice@example.com / Password123! (adresse id 1 existante).
- Burger Factory ; « Classic Burger » (id 1) à 11,90 €.

## Étapes
1. Se connecter en tant qu'Alice.
2. `POST /cart/add/1` avec `quantity=2`.
3. `POST /checkout` avec `confirm=1, address_id=1, payment_method=cash, cash_received=5, coupon=, customer_note=QA`.
4. `curl -b cj.txt -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/orders/5` (session Alice dans `cj.txt`).

Variante API (non exécutée dans la campagne) : `POST /api/orders` avec `"payment_method":"cash","cash_received":5`.

## Résultat attendu
Refus : espèces fournies (5,00 €) inférieures au total (26,79 €).

## Résultat obtenu
Commande #5 confirmée, `payment_status` paid ; `cash_received` 5.0, `total` 26.79, `change_due` -21.79.

## Preuve
- `docs/evidence/screenshots/BUG-005.png`
- `docs/evidence/TC-ERR-06.json`
- `docs/evidence/_campaign_script.py` (l. 171-176)

## Impact
Commande marquée payée alors que le paiement est insuffisant : perte financière directe.

## Piste de cause (lecture seule)
- `app/routes/orders.py:39-40` : aucun contrôle `cash_received >= total`, `change_due` calculé sans borne.
- `app/routes/api.py:180-187` : même absence de validation côté API.
