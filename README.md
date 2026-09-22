# ScanToExcel

Convertit une facture (PDF ou image) en données Excel/CSV exploitables. Voir `/prototype` pour la maquette interactive d'origine (artifact Claude) qui a servi de référence à ce scaffold.

## Stack

| Élément | Choix |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind |
| API | FastAPI (Python) |
| Base de données | PostgreSQL |
| Auth | Supabase Auth (JWT vérifié côté API) |
| Stockage fichiers | S3-compatible (S3 / Cloudflare R2 / Supabase Storage) |
| File d'attente | Redis + Celery |
| Extraction | API Claude (multimodal), voir `backend/app/services/extraction.py` |
| Export | openpyxl / csv |
| Paiement | Stripe (Phase 3, non branché) |

## Démarrer en local

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
# renseigne ANTHROPIC_API_KEY, les identifiants Supabase, S3/R2 et Stripe dans ces fichiers

docker compose up --build
```

`docker compose` lance : `db` (Postgres), `redis`, `api` (FastAPI), `worker` (Celery, extraction async) et `beat` (Celery beat, purge programmée des fichiers originaux). Après le premier démarrage, applique les migrations :

```bash
docker compose exec api alembic upgrade head
```

- API : http://localhost:8000/api/v1/health
- Frontend : http://localhost:3000

Sans Docker (dev rapide) :

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# worker (dans un autre terminal)
celery -A app.workers.celery_app worker --loglevel=info

# beat, pour la purge programmée des fichiers originaux (dans un 3e terminal)
celery -A app.workers.celery_app beat --loglevel=info

# frontend
cd frontend
npm install
npm run dev
```

### Tests backend

```bash
cd backend
pip install -r requirements.txt
pytest
```

13 tests couvrent les règles de validation d'une facture extraite, l'application des limites du plan gratuit (y compris le cas d'un plan payant actif vs résilié) et la génération des exports Excel/CSV. Ils tournent sans base de données réelle (session Postgres mockée / objets en mémoire).

### Webhook Stripe en local

```bash
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

Copie le secret affiché (`whsec_...`) dans `STRIPE_WEBHOOK_SECRET`.

## État d'avancement (voir plan de développement)

- [x] Phase 1 — Prototype : upload, un seul type de document, extraction → JSON, export Excel, stockage temporaire (voir l'artifact publié)
- [x] Phase 2 — MVP utilisable : auth Supabase (lien magique + mot de passe, middleware de protection des routes), historique, traitement asynchrone (Celery), gestion d'erreurs, limites du plan gratuit appliquées à l'upload (402 si dépassement), purge programmée des fichiers originaux (Celery beat), Docker.
- [x] Phase 3 — Monétisation : Stripe Checkout (plans Personnel/Pro), portail client, webhook de synchronisation d'abonnement, page `/facturation` avec consommation réelle du mois (barre de progression, alerte visuelle à 80 %).
- [x] Emails transactionnels : confirmation d'extraction (envoyée par le worker après traitement) et alerte à 80 % du quota gratuit (déclenchée une seule fois par période) — via Resend, silencieux si `RESEND_API_KEY` n'est pas configurée.
- [x] Page de détail document (`/documents/[id]`) : aperçu du fichier original (image ou lien PDF via URL signée), fiche extraite éditable, suivi en direct pendant l'extraction, suppression.
- [x] Phase 4 — Produit commercial :
  - **Contrôles SIRET/TVA FR** : validation par clé de Luhn (SIREN/SIRET) et clé de TVA intracommunautaire (`backend/app/services/french_tax_ids.py`, porté en JS dans `frontend/lib/frenchTaxIds.ts` pour un retour immédiat côté formulaire) — intégrée aux avertissements de la fiche extraite.
  - **Export comptable FEC** : le Fichier des Écritures Comptables, format standardisé par l'administration fiscale française et importable tel quel dans Pennylane, Sage, QuickBooks, Indy, etc. (`backend/app/services/fec_export.py`, bouton "Export comptable (FEC)" sur le tableau de bord). Les comptes utilisés (achats/TVA/fournisseurs) sont génériques et configurables (`FEC_ACCOUNT_*`) — à ajuster au plan comptable réel de l'utilisateur.
  - **SEO** : landing page publique à `/` (l'app privée a été déplacée vers `/app`), métadonnées OpenGraph, `robots.ts`/`sitemap.ts`, JSON-LD `SoftwareApplication`.
  - **i18n** : landing page bilingue FR/EN via `?lang=en` (`hreflang` + `alternates` corrects). Volontairement limité à la landing page pour cette V1 — l'app authentifiée reste en français uniquement ; une i18n complète (sous-chemins `/en/*`, traduction de `/app`) est un chantier à part si le besoin se confirme.

## Notes importantes

- `backend/app/services/extraction.py` appelle l'API Claude directement avec ta propre clé (`ANTHROPIC_API_KEY`), pas le mécanisme `sample` du prototype (qui appartient au viewer d'un artifact) — c'est le bon composant à faire évoluer si tu changes de fournisseur OCR/LLM.
- Les modèles ne valident pas encore l'unicité ni les contraintes métier avancées (SIRET, TVA FR) : à ajouter en Phase 4 selon la stratégie de différenciation.
- Le plan d'un utilisateur vit dans `subscriptions` (table locale), synchronisée par le webhook Stripe — jamais lue directement depuis l'API Stripe en chemin critique.
- La suppression automatique (`purge_expired_originals`) ne touche que le fichier source dans le stockage objet ; les données déjà extraites restent en base.
- Les emails transactionnels utilisent Resend (`RESEND_API_KEY`, `EMAIL_FROM`) ; sans clé configurée, l'envoi est simplement loggé et ignoré — aucun impact sur le reste du pipeline.
- Les identifiants FR (SIREN/SIRET/TVA) sont contrôlés par formule (clé de Luhn, clé de TVA intracommunautaire) : ça détecte les fautes de frappe/erreurs d'OCR, mais ça ne vérifie pas qu'un identifiant *existe réellement* (pas d'appel à l'API Sirene) — à ajouter si besoin.
- L'export FEC couvre le cas simple (une écriture Achats/TVA/Fournisseurs par facture) ; un cabinet comptable voudra probablement affiner le plan comptable (`FEC_ACCOUNT_*`) et gérer la ventilation multi-comptes par ligne, hors scope de cette V1.
