# BUG-016 — La déconnexion se fait par simple requête GET, sans protection CSRF

- **ID** : BUG-016
- **Cas de test lié** : TC-ERR-13
- **Sévérité** : Mineure
- **Priorité** : P3

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Compte alice@example.com / Password123! connecté.

## Étapes de reproduction

1. Se connecter avec alice@example.com / Password123! ; vérifier l'accès à http://127.0.0.1:5000/profile/ (HTTP 200).
2. Ouvrir http://127.0.0.1:5000/logout (simple GET, sans POST ni jeton CSRF) ; une balise `<img src="http://127.0.0.1:5000/logout">` sur une page tierce produit le même effet.
3. Recharger http://127.0.0.1:5000/profile/.

## Résultat attendu

La déconnexion s'effectue via POST avec jeton CSRF ; un GET ne doit pas modifier l'état de la session.

## Résultat obtenu

`GET /logout` → redirection vers `/` ; session fermée (connecté avant = True, après = False) ; `GET /profile/` redirige ensuite vers `/login?next=%2Fprofile%2F`.

## Preuve

- `docs/evidence/screenshots/BUG-016.png`
- `docs/evidence/TC-ERR-13.json`

## Impact

Déconnexion forcée d'un utilisateur par un site tiers (CSRF « logout ») : nuisance, perte de panier/session.

## Piste de cause (lecture seule, `app/`)

`app/routes/auth.py:49-52` : `@auth_bp.get("/logout")` appelle `logout_user()` directement.
