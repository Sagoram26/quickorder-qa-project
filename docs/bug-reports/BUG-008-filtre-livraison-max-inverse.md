# BUG-008 — Filtre « livraison max » inversé

- **ID** : BUG-008
- **Cas de test lié** : TC-LIM-05
- **Sévérité** : Majeure — **Priorité** : P2

## Contexte
- **Version** : QuickOrder V3.1
- **Environnement** : Windows 11, Chrome, application Flask locale (http://127.0.0.1:5000)

## Préconditions
- Base de données réinitialisée avec les données seed (`seed.py`) ; aucun compte requis.
- Frais de livraison : Green Kitchen 1,99 €, Pizza Roma 2,49 €, Burger Factory 2,99 €, Couscous Atlas 2,99 €, Night Sushi 2,99 €, Tokyo Bowl 3,49 €.

## Étapes
1. Ouvrir `http://127.0.0.1:5000/?max_delivery=2.50` (ou utiliser le filtre de livraison de la page d'accueil).
2. Lire la liste des restaurants affichés.

## Résultat attendu
Uniquement les restaurants dont les frais sont inférieurs ou égaux à 2,50 € : Green Kitchen (1,99 €) et Pizza Roma (2,49 €).

## Résultat obtenu
Affichés : Burger Factory, Tokyo Bowl, Couscous Atlas, Night Sushi (frais > 2,50 €) ; Green Kitchen et Pizza Roma absents.

## Preuve
- `docs/evidence/screenshots/BUG-008.png`
- `docs/evidence/TC-LIM-05.json`
- `docs/evidence/_campaign_script.py` (l. 140-142)

## Impact
Le filtre renvoie l'inverse de ce qui est demandé : fonctionnalité inutilisable qui trompe l'utilisateur.

## Piste de cause (lecture seule)
- `app/routes/main.py:24-25` : `Restaurant.delivery_fee >= max_delivery` au lieu de `<=` (commentaire « INTENTIONAL QA BUG » l. 16-17).
