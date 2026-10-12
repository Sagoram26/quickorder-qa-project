# BUG-009 — Un administrateur peut faire repasser une commande livrée au statut « confirmed » (transition arrière acceptée)

- **ID** : BUG-009
- **Cas de test lié** : TC-REG-06
- **Sévérité** : Majeure
- **Priorité** : P2

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Compte admin : admin@quickorder.local / Admin123! ; la commande #1 existe au statut `delivered` (données de seed).

## Étapes de reproduction

1. Ouvrir http://127.0.0.1:5000/login et se connecter avec admin@quickorder.local / Admin123!.
2. Ouvrir http://127.0.0.1:5000/admin/ et repérer la commande #1 (statut `delivered`).
3. Dans la liste de statuts de la commande #1, choisir `confirmed` (équivalent : `POST /admin/orders/1/status` avec `status=confirmed`).
4. Consulter `GET /api/orders/1` (session admin) ou le détail de la commande.

## Résultat attendu

Une commande `delivered` est un état final : le passage à `confirmed` doit être refusé avec un message d'erreur (ex. « Transition de statut invalide ») et le statut doit rester `delivered`.

## Résultat obtenu

`POST /admin/orders/1/status` → HTTP 200 (après redirection vers `/admin/`) avec le message « Statut mis à jour. ». `GET /api/orders/1` retourne `"status": "confirmed"` (total 18.39, payment_status `paid`). Le retour arrière est accepté.

## Preuve

- `docs/evidence/TC-REG-06.json`
- `docs/evidence/screenshots/BUG-009.png`

## Impact

Une commande déjà livrée et payée repasse à « confirmed » : incohérence du suivi, statistiques faussées, risque de double livraison/remboursement ; vaut aussi pour delivered → cancelled (commentaire du code).

## Piste de cause (lecture seule, `app/`)

`app/routes/admin.py:29-43` (`update_order_status`) : seule l'appartenance à l'ensemble `allowed` (l.34) est vérifiée, puis `order.status = status` (l.40) sans matrice de transitions. Le commentaire l.37-38 signale le défaut. À noter : la route n'est protégée que par `@login_required` (l.30), sans contrôle de rôle visible dans la fonction.
