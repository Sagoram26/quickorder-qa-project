# QuickOrder V3.1

QuickOrder est une application web pédagogique de commande de repas développée avec **Python, Flask, Flask-SQLAlchemy et SQLite**.

Elle est destinée au cours **Tests et qualité des solutions numériques**. Le but n'est pas seulement de faire fonctionner l'application : les étudiants doivent l'auditer comme une équipe QA, concevoir une stratégie de test, écrire des cas de test, tester l'interface et l'API, documenter les anomalies et proposer des améliorations.

## Fonctionnalités

- inscription / connexion / déconnexion
- comptes client et administrateur
- restaurants et catégories
- recherche et filtres
- tri par note, prix de livraison et délai
- menus et catégories de produits
- produits végétariens
- panier mono-restaurant
- modification et suppression du panier
- coupons avec minimum, expiration et plafond de réduction
- checkout
- adresses de livraison
- paiement simulé
- commandes et suivi de statut
- annulation de commande
- recommander une ancienne commande
- favoris restaurants
- avis et notes
- espace profil
- espace administrateur
- API REST
- Swagger UI / OpenAPI
- Docker / Docker Compose
- tests automatisés de base

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|---|---|---|
| Client | `alice@example.com` | `Password123!` |
| Client | `bob@example.com` | `Password123!` |
| Admin | `admin@quickorder.local` | `Admin123!` |

## Démarrage rapide

### Option A — Python + environnement virtuel

Windows PowerShell :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed.py
python run.py
```

macOS / Linux :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python seed.py
python run.py
```

Application : http://127.0.0.1:5000

Swagger : http://127.0.0.1:5000/docs/

Clé API Swagger : `quickorder-demo-key` → bouton **Authorize**.


### Option B — Docker Compose

Après installation de Docker Desktop :

```bash
docker compose up --build
```

Puis : http://127.0.0.1:5000

Swagger : http://127.0.0.1:5000/docs/

Clé API Swagger : `quickorder-demo-key` → bouton **Authorize**.

Arrêter :

```bash
docker compose down
```

Voir les logs :

```bash
docker compose logs -f
```

Le volume `quickorder_data` conserve la base SQLite entre les redémarrages. Pour repartir d'une base propre :

```bash
docker compose down -v
docker compose up --build
```

## Tests

Avec le venv activé :

```bash
pytest -q
```

## Documentation pédagogique

- `docs/INSTALLATION.md` — installation complète Windows / macOS / Linux et Docker
- `docs/API.md` — guide de test de l'API et configuration de la clé Swagger
- `docs/STUDENT_BRIEF.md` — sujet à distribuer aux étudiants

## Audit qualité (livrables QA)

Résultat de la campagne: 36 cas exécutés, 20 Pass, 16 Fail, 16 bugs documentés. Recommandation: **No-Go**.

| Livrable | Fichier |
|---|---|
| Stratégie de test | `docs/test-strategy.md` |
| Matrice de risques | `docs/risk-matrix.md` |
| Cas de test (36) | `docs/test-cases.xlsx` |
| Rapport d'exécution et Go / No-Go | `docs/execution-report.md` |
| Bug reports (16) | `docs/bug-reports/` |
| Retours utilisateurs | `docs/user-feedback.md` |
| Plan d'amélioration | `docs/improvement-plan.md` |
| Preuves (JSON requêtes/réponses, captures) | `docs/evidence/` |

Rejouer la campagne (réinitialise la base, app lancée sur `127.0.0.1:5000`) : `python docs/evidence/_campaign_script.py`.

## Important

QuickOrder est volontairement une application pédagogique et ne doit pas être considérée comme une application de production. Certains choix et certaines anomalies sont conservés pour créer des situations de test réalistes.
