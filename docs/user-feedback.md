# Tests utilisateurs - QuickOrder

> **ATTENTION : ces retours sont des sessions simulées (personas) et non de vrais utilisateurs ; à remplacer par de vrais retours avant toute décision.**

Les problèmes décrits sont tous rattachés à des bugs réellement prouvés (voir `docs/bug-reports/` et `docs/evidence/_results.json`). Les verbatims sont fictifs. La « fréquence » est celle observée dans la simulation (x/2 personas), pas une statistique.

## Profils

| Id | Profil | Contexte d'usage |
|----|--------|------------------|
| P1 | Léa, 22 ans, étudiante, mobile-first | Smartphone, pressée, petit budget, utilise les codes promo et PayPal |
| P2 | Marc, 45 ans, salarié, peu technophile | Ordinateur au bureau, paie en espèces, lit peu les messages, craint les erreurs |

## Scénario A - Chercher un restaurant et filtrer par frais de livraison

| # | Profil | Contexte | Problème | Fréquence | Impact | Verbatim | Hypothèse d'amélioration | Priorité |
|---|--------|----------|----------|-----------|--------|----------|--------------------------|----------|
| A1 | P1 | Mobile, cherche « sans frais de livraison » | Le filtre livraison est inversé : les restaurants payants s'affichent (BUG-008) | 2/2 | Élevé : résultats faux, perte de confiance | « Je coche livraison gratuite et je vois que des restaurants à 3,50 €. C'est cassé. » | Corriger la condition du filtre et ajouter un test d'API | Haute |
| A2 | P2 | Cherche « pizza aux champignons », terme présent dans la description | La recherche ignore la description (BUG-014) | 1/2 | Moyen : il croit que le plat n'existe pas | « J'ai tapé champignons, rien. Donc ils n'en ont pas ? » | Étendre la recherche à nom + description + cuisine | Moyenne |
| A3 | P2 | Ouvre un restaurant fermé depuis la liste | Le restaurant fermé reste commandable, aucun blocage visible (BUG-003) | 1/2 | Critique : commande jamais livrée | « C'est marqué fermé mais il me laisse ajouter au panier. » | Bloquer l'ajout et le checkout, griser la carte | Haute |

## Scénario B - Commander avec coupon et payer (carte / PayPal / espèces)

| # | Profil | Contexte | Problème | Fréquence | Impact | Verbatim | Hypothèse d'amélioration | Priorité |
|---|--------|----------|----------|-----------|--------|----------|--------------------------|----------|
| B1 | P1 | Applique ATLAS15, annoncé « -15 % » | Seulement 10 % appliqués (BUG-007) | 1/2 | Moyen : promesse non tenue, confiance | « Ça disait 15 % et j'ai 10 %. On m'a menti ? » | Une seule source de vérité pour le taux ; afficher la remise calculée | Haute |
| B2 | P1 | Paie via PayPal | La commande est créée deux fois (BUG-006) | 1/2 | Critique : double facturation | « J'ai deux commandes pour un seul paiement ! » | Supprimer le doublon, rendre la création idempotente | Haute |
| B3 | P2 | Panier sous le minimum du restaurant | La commande passe malgré le minimum (BUG-004) | 1/2 | Moyen : pertes pour le restaurant, incohérence | « Ça m'a laissé commander 8 €, alors qu'il faut 15 €. Le resto va râler. » | Contrôle serveur du minimum avec message clair | Moyenne |
| B4 | P2 | Espèces : indique 10 € pour une commande de 24 € | Montant insuffisant accepté (BUG-005) | 1/2 | Critique : litige à la livraison | « J'ai mis 10 € pour payer 24 €, il a validé sans rien dire. » | Valider espèces >= total côté serveur | Haute |
| B5 | P2 | Laisse l'adresse vide | Commande acceptée sans adresse (BUG-015) | 1/2 | Moyen : livraison impossible | « Je n'ai pas rempli l'adresse et ça a marché. Où ils livrent ? » | Champ obligatoire + validation serveur | Moyenne |
| B6 | P1 | Saisit un coupon invalide depuis l'appli (API) | Le coupon invalide est ignoré sans erreur (BUG-013) | 1/2 | Moyen : elle croit avoir une remise | « Mon code n'a rien fait et personne ne me dit pourquoi. » | Renvoyer 400 explicite | Moyenne |

## Scénario C - Annuler puis recommander une commande

| # | Profil | Contexte | Problème | Fréquence | Impact | Verbatim | Hypothèse d'amélioration | Priorité |
|---|--------|----------|----------|-----------|--------|----------|--------------------------|----------|
| C1 | P1 | Recommande un plat dont le stock est à 0 | Ajout possible malgré stock 0 (BUG-001) | 1/2 | Élevé : commande impossible à honorer | « Le plat est épuisé mais je peux le commander quand même. » | Contrôle du stock à l'ajout et au checkout, transaction atomique | Haute |
| C2 | P1 | Plusieurs commandes enchaînées | Le stock devient négatif (BUG-002) | 1/2 | Élevé : survente | « Ils m'ont dit plus tard qu'il n'y en avait plus. » | Décrément atomique avec contrainte >= 0 | Haute |
| C3 | P2 | Après annulation, la commande repasse à un statut antérieur côté admin | Retour arrière de statut possible (BUG-009) | 1/2 | Moyen : annulation « ressuscitée », suivi faux | « Mon annulation est redevenue en préparation. » | Machine d'états avec transitions autorisées | Moyenne |
| C4 | P2 | Laisse un avis sur une commande jamais passée | Avis accepté sans commande (BUG-010) | 1/2 | Faible/Moyen : avis faux | « J'ai pu noter un resto où je n'ai jamais commandé. » | N'autoriser l'avis qu'après commande livrée | Basse |

## Observations sécurité (hors parcours, constatées par QA)

Les personas ne les perçoivent pas, mais elles pèsent sur la priorité : BUG-011 (open redirect au login), BUG-012 (API sans session = compte alice, Critique), BUG-016 (déconnexion en GET). Aucun verbatim : ces risques sont invisibles pour l'utilisateur.

## Synthèse priorisée

| Rang | Observation | Bug | Gravité | Fréquence | Priorité |
|------|-------------|-----|---------|-----------|----------|
| 1 | Double commande PayPal | BUG-006 | Critique | 1/2 | Haute |
| 2 | Espèces insuffisantes acceptées | BUG-005 | Critique | 1/2 | Haute |
| 3 | Restaurant fermé commandable | BUG-003 | Critique | 1/2 | Haute |
| 4 | Stock 0 ajoutable / stock négatif | BUG-001, BUG-002 | Élevée | 1/2 | Haute |
| 5 | Filtre livraison inversé | BUG-008 | Élevée | 2/2 | Haute |
| 6 | ATLAS15 10 % au lieu de 15 % | BUG-007 | Moyenne | 1/2 | Haute |
| 7 | Minimum de commande ignoré | BUG-004 | Moyenne | 1/2 | Moyenne |
| 8 | Adresse vide acceptée | BUG-015 | Moyenne | 1/2 | Moyenne |
| 9 | Coupon invalide ignoré (API) | BUG-013 | Moyenne | 1/2 | Moyenne |
| 10 | Retour arrière de statut | BUG-009 | Moyenne | 1/2 | Moyenne |
| 11 | Recherche ignore la description | BUG-014 | Faible | 1/2 | Moyenne |
| 12 | Avis sans commande | BUG-010 | Faible | 1/2 | Basse |

## Grille vierge pour sessions réelles

À dupliquer pour chaque participant réel (≥ 2 personnes × 3 scénarios A, B, C) et à substituer aux observations simulées ci-dessus.

| Champ | À renseigner |
|---|---|
| Participant (profil, âge, aisance numérique) | |
| Scénario (A, B ou C) | |
| Contexte (appareil, navigateur, compte utilisé) | |
| Problème observé | |
| Fréquence (n fois sur n essais) | |
| Impact (bloquant, gênant, cosmétique) | |
| Verbatim (citation exacte) | |
| Hypothèse d'amélioration | |
| Priorité (P1 à P4) et bug lié | |
