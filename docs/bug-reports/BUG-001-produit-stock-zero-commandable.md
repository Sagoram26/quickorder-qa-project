# BUG-001 — Produit en rupture (stock 0) visible et ajoutable au panier

- **ID** : BUG-001
- **Cas de test lié** : TC-ERR-04
- **Sévérité** : Majeure — **Priorité** : P2

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`).
- Compte client : alice@example.com / Password123! (adresse id 1 existante).
- Seed : « Veggie Burger » (id 4, Burger Factory, 12,90 €) a un stock de 0 (`seed.py:14`).

## Étapes
1. Se connecter en tant qu'Alice (UI `/login`).
2. Ouvrir `/restaurant/1` (Burger Factory) : « Veggie Burger » est listé.
3. Cliquer sur « Ajouter au panier » (équivalent : `POST /cart/add/4` avec `quantity=1`).
4. Ouvrir `/cart`.

## Résultat attendu
Produit en rupture masqué ou marqué « Indisponible », ajout au panier refusé avec un message d'erreur.

## Résultat obtenu
- Veggie Burger (stock 0) visible sur la page restaurant : True.
- `POST /cart/add/4` → HTTP 200, message « Veggie Burger ajouté au panier. ».
- `/cart` : « Veggie Burger 12.90 € … Sous-total 12.90 € Livraison 2.99 € Total 15.89 € » ; ajouté au panier = True.

## Preuve
- `docs/evidence/screenshots/BUG-001.png`
- `docs/evidence/TC-ERR-04.json`
- `docs/evidence/_campaign_script.py` (l. 165-169)

## Impact
Un client peut commander un produit qui n'est plus en stock ; risque de commande non livrable et de frustration client.

## Piste de cause (lecture seule)
- `app/routes/main.py:49-50` : la requête produits filtre seulement `available=True`, pas `stock > 0`.
- `app/routes/shop.py:16-27` : la route d'ajout vérifie `product.available` mais jamais `product.stock`.
