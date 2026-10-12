# BUG-011 — Redirection ouverte (open redirect) vers un site externe via le paramètre ?next= à la connexion

- **ID** : BUG-011
- **Cas de test lié** : TC-ERR-10
- **Sévérité** : Majeure (sécurité)
- **Priorité** : P2

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Compte alice@example.com / Password123! ; utilisateur non connecté.

## Étapes de reproduction

1. Exécuter : `curl -i -X POST "http://127.0.0.1:5000/login?next=https://evil.example/phish" -d "email=alice@example.com&password=Password123!"`.
2. Ou via navigateur : ouvrir `http://127.0.0.1:5000/login?next=https://evil.example/phish`, se connecter avec alice@example.com / Password123!.
3. Observer l'en-tête `Location` de la réponse.

## Résultat attendu

Seules les URL relatives internes sont acceptées pour `next` ; une URL externe est ignorée et l'utilisateur est redirigé vers `/`.

## Résultat obtenu

HTTP 302 avec `Location: https://evil.example/phish` (corps : « You should be redirected automatically to the target URL: https://evil.example/phish »).

## Preuve

- `docs/evidence/TC-ERR-10.json`
- `docs/evidence/screenshots/BUG-011.png` (page `https://evil.example/` interceptée en local par `agent-browser network route`, sans accès réseau externe; atteinte après un login réel avec `?next=https://evil.example`)

## Impact

Phishing : un lien légitime QuickOrder renvoie l'utilisateur, juste après authentification, vers un site contrôlé par l'attaquant (OWASP A01 – Unvalidated Redirects).

## Piste de cause (lecture seule, `app/`)

`app/routes/auth.py:44` : `return redirect(request.args.get("next") or url_for("main.index"))` sans validation (hôte/schéma).
