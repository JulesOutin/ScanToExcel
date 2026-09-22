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
# renseigne ANTHROPIC_API_KEY, les identifiants Supabase et S3/R2 dans ces fichiers

docker compose up --build
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

# frontend
cd frontend
npm install
npm run dev
```

## État d'avancement (voir plan de développement)

- [x] Phase 1 — Prototype : upload, un seul type de document, extraction → JSON, export Excel, stockage temporaire (voir l'artifact publié)
- [~] Phase 2 — MVP utilisable : ce scaffold pose auth, historique, traitement asynchrone, gestion d'erreurs, Docker. **Manque encore** : page de login Supabase, page de détail document dédiée (`app/documents/[id]`), limites d'usage réellement appliquées, suppression automatique programmée des fichiers originaux.
- [ ] Phase 3 — Monétisation : Stripe, plans, compteur de pages.
- [ ] Phase 4 — Produit commercial : SEO, i18n, intégrations comptables.

## Notes importantes

- `backend/app/services/extraction.py` appelle l'API Claude directement avec ta propre clé (`ANTHROPIC_API_KEY`), pas le mécanisme `sample` du prototype (qui appartient au viewer d'un artifact) — c'est le bon composant à faire évoluer si tu changes de fournisseur OCR/LLM.
- Les modèles ne valident pas encore l'unicité ni les contraintes métier avancées (SIRET, TVA FR) : à ajouter en Phase 4 selon la stratégie de différenciation.
- Aucun test automatisé n'est inclus dans ce scaffold initial.
