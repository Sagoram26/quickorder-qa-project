# BUG-015 — Une adresse vide est créée à l'inscription et acceptée au checkout (commande sans adresse de livraison)

- **ID** : BUG-015
- **Cas de test lié** : TC-ERR-12
- **Sévérité** : Majeure
- **Priorité** : P2

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Aucun compte qa.addr@example.com existant.

## Étapes de reproduction

1. Ouvrir http://127.0.0.1:5000/register et créer un compte : nom « QA Adresse », email qa.addr@example.com, mot de passe Password123!.
2. Ajouter 2 × Classic Burger (produit #1) au panier (`POST /cart/add/1`, quantity=2).
3. Ouvrir http://127.0.0.1:5000/checkout : observer l'adresse proposée.
4. Confirmer la commande par carte (`POST /checkout`, confirm=1, address_id=5, payment_method=card).

## Résultat attendu

L'inscription ne crée pas d'adresse vide ; le checkout exige une adresse complète (rue, code postal, ville) et refuse la commande sinon.

## Résultat obtenu

Le checkout propose « Domicile — , » (adresse vide). La commande #13 est confirmée (« Commande confirmée ! », total 26.79 €, paiement `paid · card`) sans aucune adresse de livraison réelle.

## Preuve

- `docs/evidence/TC-ERR-12.json`
- `docs/evidence/screenshots/BUG-015.png`

## Impact

Commandes payées non livrables ; litiges et remboursements ; données d'adresse invalides en base.

## Piste de cause (lecture seule, `app/`)

`app/routes/auth.py:27` : `Address(..., street="", postal_code="", city="", is_default=True)` créée à l'inscription ; `app/routes/orders.py:94-98` : le checkout ne vérifie que l'existence/appartenance de l'adresse (`if not address`), pas son contenu.
