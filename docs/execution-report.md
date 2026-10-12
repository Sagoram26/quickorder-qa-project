# Rapport d'exécution - Campagne QA QuickOrder

## 1. Résumé

| Indicateur | Valeur |
|---|---|
| Cas exécutés | 36 |
| Pass | 20 |
| Fail | 16 |
| Blocked | 0 |
| Skipped | 0 |
| Taux de réussite | 55,6 % |

Détail des cas : `docs/test-cases.xlsx`. Preuves : `docs/evidence/TC-*.json` (traces requête/réponse) et `docs/evidence/screenshots/BUG-xxx.png`.

## 2. Résultats par catégorie

| Catégorie | Total | Pass | Fail |
|---|---|---|---|
| Nominal | 7 | 7 | 0 |
| Limite | 8 | 5 | 3 |
| Erreur | 13 | 6 | 7 |
| Règle métier | 8 | 2 | 6 |
| **Total** | **36** | **20** | **16** |

## 3. Échecs, bugs liés et sévérité

| Cas | Bug | Sévérité | Constat |
|---|---|---|---|
| TC-ERR-04 | BUG-001 | Majeure | Produit en rupture (stock 0) ajouté au panier |
| TC-LIM-06 | BUG-002 | Majeure | Commande > stock acceptée, stock final négatif (-1) |
| TC-REG-02 | BUG-003 | Critique | Commande acceptée chez un restaurant fermé (UI et API) |
| TC-REG-03 | BUG-004 | Majeure | Minimum de commande (20 €) non appliqué (commande à 3,50 €) |
| TC-ERR-06 | BUG-005 | Critique | Paiement espèces de 5 € pour 26,79 € accepté, commande payée (change_due -21,79) |
| TC-REG-05 | BUG-006 | Critique | Un paiement PayPal crée 2 commandes |
| TC-REG-04 | BUG-007 | Majeure | ATLAS15 annoncé -15 % applique 10 % |
| TC-LIM-05 | BUG-008 | Majeure | Filtre livraison max 2.50 € retourne aussi des restaurants plus chers |
| TC-REG-06 | BUG-009 | Majeure | Commande livrée repassée à confirmed par l'admin |
| TC-REG-07 | BUG-010 | Mineure | Avis publié sans commande préalable |
| TC-ERR-10 | BUG-011 | Majeure (sécurité) | Redirection ouverte via `next` vers un domaine externe |
| TC-ERR-09 | BUG-012 | Critique (sécurité) | `GET /api/orders` avec la seule clé API retourne les commandes d'Alice |
| TC-ERR-07 | BUG-013 | Mineure | Coupon inexistant accepté silencieusement (HTTP 201, remise 0) |
| TC-LIM-08 | BUG-014 | Mineure | Recherche ignore la description des restaurants |
| TC-ERR-12 | BUG-015 | Majeure | Commande validée sans adresse de livraison |
| TC-ERR-13 | BUG-016 | Mineure | Déconnexion déclenchée par simple GET /logout (CSRF) |

Répartition des 16 bugs : 4 Critique (003, 005, 006, 012), 8 Majeure (001, 002, 004, 007, 008, 009, 011, 015), 4 Mineure (010, 013, 014, 016).

## 4. Principaux risques

- **Financier** : paiement espèces insuffisant accepté (BUG-005), doublon de commandes PayPal (BUG-006), coupon ATLAS15 incorrect (BUG-007), minimum de commande ignoré (BUG-004).
- **Sécurité / confidentialité** : exposition des commandes clients par la clé API seule (BUG-012), redirection ouverte exploitable pour le phishing (BUG-011), déconnexion CSRF (BUG-016).
- **Opérationnel** : commandes sur restaurant fermé (BUG-003), stock négatif et produits en rupture vendus (BUG-001, BUG-002), livraison sans adresse (BUG-015).
- **Intégrité** : transitions de statut incohérentes (BUG-009), avis non vérifiés (BUG-010).

Observation : le test pytest existant `tests/test_smoke.py::test_api_orders_with_key` échoue (`AttributeError: 'NoneType'` lorsque l'utilisateur alice est absente). Ce comportement est lié à BUG-012 : l'endpoint `/api/orders` dépend d'un utilisateur par défaut (alice) au lieu d'une identification réelle.

## 5. Environnement

- Windows 11, Python 3.10.6, Flask 3.1.1
- Chrome piloté via agent-browser (captures), bibliothèque `requests`
- Application locale `http://127.0.0.1:5000`, base réinitialisée par `seed.py` avant la campagne
- Clé API de démonstration via en-tête `X-API-Key`

## 6. Méthode

- **UI** : requêtes HTTP de formulaire (sessions `requests`), avec captures navigateur des défauts dans `docs/evidence/screenshots/BUG-xxx.png`.
- **API** : appels `requests` avec en-tête `X-API-Key`.
- Chaque cas enregistre statut, résultat obtenu et trace complète (`docs/evidence/TC-*.json`) ; synthèse dans `_results.json`. Script : `docs/evidence/_campaign_script.py`.
- **Postman/newman** : la collection `docs/quickorder-api.postman_collection.json` a été exécutée avec newman (smoke test complémentaire, hors des 36 cas) : 12 requêtes exécutées, 0 en échec technique, mais 0 assertion (la collection ne contient aucun script de test), donc 0 assertion passée / 0 échouée ; les statuts HTTP sont lus à la main dans la sortie. Preuves : `docs/evidence/postman-run.txt` et `docs/evidence/postman-run.json`.
- Le code de l'application (`app/`) n'a pas été modifié.

## 7. Limites de la campagne

- Couverture limitée à 36 cas ; pas de tests de charge, de concurrence ni de performance.
- UI testée par requêtes HTTP, pas par scénarios navigateur complets : rendu visuel, accessibilité et responsive non évalués.
- Un seul navigateur et un seul environnement local ; pas de compatibilité multi-navigateurs.
- Les cas dépendent de l'état de la base (réinitialisée par `seed.py`) et s'exécutent à la suite ; un échec peut influencer les suivants (stock, commandes).
- Pas de tests de sécurité approfondis (injection, XSS, gestion des sessions) au-delà des cas listés.
- Les assertions sont automatisées ; certaines sont déduites du comportement observé et des règles du brief.

## 8. Revalidation

Aucune correction n'a été livrée à ce jour : les 16 échecs restent ouverts. Après correction, rejouer la campagne avec `python docs/evidence/_campaign_script.py` (serveur lancé sur le port 5000), puis régénérer les résultats et mettre à jour `docs/test-cases.xlsx`. Chaque bug corrigé doit être revalidé par son cas lié (voir tableau section 3) et par un test de non-régression sur les cas Pass.

## 9. Recommandation : No-Go

**Recommandation : No-Go pour la mise en production.**

- 4 bugs critiques ouverts touchant l'argent et les données : restaurant fermé acceptant des commandes (BUG-003), espèces insuffisantes acceptées (BUG-005), doublon de commandes PayPal (BUG-006), fuite des commandes via API (BUG-012).
- 8 bugs majeurs, dont une redirection ouverte (BUG-011), des règles de stock, de minimum et de coupon non respectées.
- Seuls 55,6 % des cas passent ; les catégories Règle métier (25 %) et Erreur (46 %) sont les plus faibles, là où le risque métier est le plus élevé.
- Aucune correction ni revalidation n'existe encore.

Conditions pour passer en Go : corriger au minimum tous les bugs critiques et de sécurité (BUG-003, 005, 006, 011, 012), idéalement les majeurs, rejouer la campagne avec 0 échec critique/majeur et confirmer la non-régression.
