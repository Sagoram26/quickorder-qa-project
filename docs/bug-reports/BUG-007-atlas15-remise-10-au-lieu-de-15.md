# BUG-007 — Code ATLAS15 annoncé -15 % mais 10 % appliqué

- **ID** : BUG-007
- **Cas de test lié** : TC-REG-04
- **Sévérité** : Majeure — **Priorité** : P2

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`) ; coupon ATLAS15 actif.
- Couscous Atlas affiche : « Code ATLAS15 annoncé comme -15% sur ce restaurant » (`seed.py:37`).
- Compte client : alice@example.com / Password123! (pour la variante UI).

## Étapes
1. `curl -X POST http://127.0.0.1:5000/api/coupons/validate -H "X-API-Key: quickorder-demo-key" -H "Content-Type: application/json" -d '{"code":"ATLAS15","subtotal":100}'`
2. (UI) Appliquer ATLAS15 au checkout avec un sous-total supérieur ou égal à 20 €.

## Résultat attendu
Remise de 15,0 € sur 100 € (15 %).

## Résultat obtenu
HTTP 200 : `{"code":"ATLAS15","discount":10.0,"discount_percent":10.0,"valid":true}`.

## Preuve
- `docs/evidence/screenshots/BUG-007.png`
- `docs/evidence/TC-REG-04.json`
- `docs/evidence/_campaign_script.py` (l. 213-214)

## Impact
Publicité trompeuse : le client reçoit moins que la remise annoncée.

## Piste de cause (lecture seule)
- `seed.py:88` : coupon créé avec `discount_percent=Decimal("10")` alors que l'annonce est de 15 %.
- `app/routes/orders.py:21-24` : calcul de la remise à partir de cette valeur (commentaire « INTENTIONAL QA BUG » l. 24).
