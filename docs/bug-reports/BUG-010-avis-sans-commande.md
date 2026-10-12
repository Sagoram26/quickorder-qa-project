# BUG-010 — Un client peut publier un avis sur un restaurant où il n'a jamais commandé

- **ID** : BUG-010
- **Cas de test lié** : TC-REG-07
- **Sévérité** : Mineure
- **Priorité** : P3

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Compte bob@example.com / Password123! n'ayant jamais commandé chez Green Kitchen (restaurant #3).

## Étapes de reproduction

1. Se connecter sur http://127.0.0.1:5000/login avec bob@example.com / Password123!.
2. Ouvrir http://127.0.0.1:5000/restaurant/3 (Green Kitchen).
3. Dans le formulaire d'avis, saisir note = 1 et commentaire « QA: avis sans commande », puis envoyer (équivalent : `POST /restaurant/3/review`).

## Résultat attendu

L'avis est refusé : seuls les clients ayant une commande livrée chez ce restaurant peuvent le noter.

## Résultat obtenu

`POST /restaurant/3/review` (rating=1, comment="QA: avis sans commande") → HTTP 200 sur `/restaurant/3` avec le message « Merci pour votre avis ! » : l'avis est publié (TC : « avis publié: True »).

## Preuve

- `docs/evidence/TC-REG-07.json`
- `docs/evidence/screenshots/BUG-010.png`

## Impact

Faux avis / manipulation de la note moyenne d'un restaurant ; perte de confiance dans les avis.

## Piste de cause (lecture seule, `app/`)

`app/routes/shop.py:77-92` (`review`) : aucune vérification d'une commande existante de `current_user` pour `restaurant_id` avant `db.session.add(Review(...))` (l.90). Commentaire l.89 du code.
