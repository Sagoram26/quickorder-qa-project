# Kit de sessions utilisateurs - QuickOrder

Objectif: collecter les retours **réels** exigés par le brief §6 (≥ 3 scénarios par ≥ 2 personnes). Les résultats se saisissent dans la grille de fin de `docs/user-feedback.md`, qui remplace les personas simulés.

## Préparation (5 min)

1. Lancer l'app: `python seed.py` puis `python run.py` (http://127.0.0.1:5000). Réinitialiser (`python seed.py`) entre deux participants.
2. Ouvrir l'application dans un navigateur neuf (fenêtre privée). Comptes: `alice@example.com` / `Password123!` ou `bob@example.com` / `Password123!`.
3. Prévoir: chronomètre, un outil pour noter les citations mot pour mot, un enregistrement d'écran (optionnel, avec l'accord du participant).

## Consignes au facilitateur

- Lire la tâche à voix haute; ne pas guider, ne pas corriger, ne pas expliquer l'interface.
- Demander au participant de penser à voix haute. Noter les hésitations, erreurs, retours en arrière, citations exactes.
- Ne pas collecter de données personnelles réelles: utiliser les comptes de démonstration.
- Fin de session: demander « Qu'est-ce qui vous a le plus gêné ? Qu'est-ce qui vous a surpris ? ».

## Scénarios

### A - Trouver un restaurant avec livraison peu chère
Tâche lue au participant: « Vous voulez un repas dont la livraison ne dépasse pas 2,50 €. Trouvez un restaurant qui convient, puis cherchez un plat avec le mot "japonaise". »
À observer: le filtre de frais de livraison (rappel BUG-008), la recherche par description (BUG-014), la lisibilité des restaurants fermés (BUG-003).

### B - Commander avec un coupon et payer
Tâche: « Commandez deux Classic Burger chez Burger Factory avec le code WELCOME10, payez en espèces avec 5 €, puis refaites avec PayPal. » (Variante: Couscous Atlas avec ATLAS15, la promo annonce -15 %.)
À observer: clarté du total, de la réduction (BUG-007), refus ou acceptation du montant espèces (BUG-005), nombre de commandes créées par PayPal (BUG-006), minimum de commande (BUG-004).

### C - Annuler puis recommander
Tâche: « Annulez votre dernière commande, puis recommandez la commande livrée d'Alice. »
À observer: visibilité du bouton d'annulation, message de confirmation, contenu du panier après « Recommander », produits en rupture (BUG-001, BUG-002).

## Fiche d'observation (une par participant et par scénario)

Reprendre les colonnes de la grille de `docs/user-feedback.md`: profil, contexte, problème, fréquence, impact, verbatim, hypothèse d'amélioration, priorité + bug lié.

## Après les sessions

1. Reporter les observations dans `docs/user-feedback.md` (supprimer les sections simulées et l'avertissement).
2. Relier chaque problème à un BUG existant ou en ouvrir un nouveau dans `docs/bug-reports/`.
3. Mettre à jour `docs/improvement-plan.md` selon la fréquence et l'impact observés.
