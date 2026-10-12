# BUG-014 — La recherche de restaurants ignore la description (UI et API)

- **ID** : BUG-014
- **Cas de test lié** : TC-LIM-08
- **Sévérité** : Mineure
- **Priorité** : P3

## Contexte

QuickOrder V3.1, Windows 11, Google Chrome, serveur Flask local (http://127.0.0.1:5000). En-tête API : `X-API-Key: quickorder-demo-key`.

## Préconditions

Visiteur anonyme ; le restaurant Tokyo Bowl a pour description « Cuisine japonaise et bowls frais ».

## Étapes de reproduction

1. Ouvrir `http://127.0.0.1:5000/?q=japonaise`.
2. Ou exécuter : `curl -H "X-API-Key: quickorder-demo-key" "http://127.0.0.1:5000/api/restaurants?q=japonaise"`.
3. Observer les résultats.

## Résultat attendu

Tokyo Bowl apparaît (le terme figure dans sa description), `count >= 1`.

## Résultat obtenu

UI : Tokyo Bowl non trouvé. API : `{"count": 0, "items": []}` (HTTP 200).

## Preuve

- `docs/evidence/TC-LIM-08.json`
- `docs/evidence/screenshots/BUG-014.png`

## Impact

Résultats de recherche incomplets : le client ne trouve pas un restaurant via les mots de sa description ; perte de commandes.

## Piste de cause (lecture seule, `app/`)

`app/routes/main.py:21` et `app/routes/api.py:73` : filtre limité à `Restaurant.name.ilike(f"%{q}%")` (description non incluse).
