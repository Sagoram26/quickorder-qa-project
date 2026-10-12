# BUG-003 — Restaurant fermé (Night Sushi) commandable en UI et via l'API

- **ID** : BUG-003
- **Cas de test lié** : TC-REG-02
- **Sévérité** : Critique — **Priorité** : P1

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`).
- Compte client : alice@example.com / Password123! (adresse id 1 existante).
- Seed : « Night Sushi » (restaurant 6) a `is_open=False` (`seed.py:74`) ; produit « Late Sushi Box » (id 24, 14,00 €).

## Étapes
1. Se connecter en tant qu'Alice.
2. `POST /cart/add/24` avec `quantity=1`.
3. `POST /checkout` avec `confirm=1, address_id=1, payment_method=card, coupon=, customer_note=QA`.
4. API (session Alice dans `cj.txt`, ouverte par `curl -c cj.txt -X POST http://127.0.0.1:5000/login -d "email=alice@example.com" -d "password=Password123!"`) :
   `curl -X POST http://127.0.0.1:5000/api/orders -H "X-API-Key: quickorder-demo-key" -H "Content-Type: application/json" -b cj.txt -d '{"items":[{"product_id":24,"quantity":1}],"payment_method":"card"}'`
5. `curl -H "X-API-Key: quickorder-demo-key" http://127.0.0.1:5000/api/restaurants` : Night Sushi est listé.

## Résultat attendu
Ajout/commande refusé (restaurant fermé) : message d'erreur en UI, HTTP 4xx en API ; restaurant fermé non proposé comme commandable.

## Résultat obtenu
- UI : commande #7 confirmée (« Night Sushi … Late Sushi Box × 1 14.00 € … Total 16.99 € Paiement paid · card »).
- API : HTTP 201, commande #8 (`restaurant_id` 6, `status` confirmed, `payment_status` paid, total 16.99).
- Night Sushi présent dans `GET /api/restaurants`.

## Preuve
- `docs/evidence/screenshots/BUG-003.png`
- `docs/evidence/TC-REG-02.json`
- `docs/evidence/_campaign_script.py` (l. 204-207)

## Impact
Commandes payées pour un restaurant qui ne peut pas les préparer ; remboursements, perte de confiance.

## Piste de cause (lecture seule)
- `app/routes/orders.py:104-105` : `restaurant.is_open` non vérifié au checkout.
- `app/routes/shop.py:16-18` : aucun contrôle à l'ajout au panier.
- `app/routes/api.py:78-80` (liste) et `api.py:180-181` (création de commande) : aucun contrôle d'ouverture.
