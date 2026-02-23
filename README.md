# AI-Powered Threat Intelligence Aggregator (Django + React)

A threat intelligence platform that uses LLMs to summarize security feeds, extract IOCs, and assess relevance. Built incrementally — each phase works on its own before moving to the next.

**Fully local**: The entire stack runs on your machine with no cloud dependencies. Fetch feeds while online, then work offline with everything stored locally.

## Tech Stack

- [x] **Backend**: Django REST Framework
- [ ] **Frontend**: React
- [x] **Database**: PostgreSQL
- [x] **AI**: Ollama (local LLMs)
- [x] **Task Queue**: Celery + Redis
- [ ] **CVE Data**: cve-search (local MongoDB, `../cve-search`)
- [x] **Vector DB**: ChromaDB (local, no cloud needed)
- [ ] **Deployment**: Docker Compose → Kubernetes

---

## Phase 1: Paper Plane — Django + One Feed ✅

**Goal**: Get Django running and pulling from a single threat intel feed.

- [x] Set up Django project with one app (`feeds`)
- [x] One model: `Article` (title, date, link, summary, source)
- [x] Management command to fetch a single RSS feed (e.g., CISA alerts)
- [x] One DRF endpoint: `GET /api/articles/` — list stored articles
- [x] SQLite is fine for now (swap to PostgreSQL later)
- [x] **Dependencies**: `djangorestframework`, `feedparser`
- [x] **Tip**: Fetch and store articles while you have internet — everything else works offline
- [x] **Done when**: You run the management command, it fetches articles, and you can see them at `/api/articles/`

---

## Phase 2: Kite — Multiple Sources + PostgreSQL ✅

**Goal**: Aggregate from multiple feeds with a real database.

- [x] Add 2-3 more RSS/Atom feeds (Krebs, US-CERT, BleepingComputer)
- [x] Switch from SQLite to PostgreSQL
- [x] Deduplicate articles by URL
- [x] Add filtering to the API: by source, date range
- [x] Database migrations and proper indexing
- [x] **Done when**: Multiple feeds are being ingested and queryable via the API

---

## Phase 3: Glider — LLM Summarization & Classification ✅

**Goal**: Use an LLM to summarize and tag articles.

- [x] Set up Ollama for local models
- [x] Send article content to Ollama's local API for:
  - [x] A one-paragraph summary
  - [x] Tags: threat type (ransomware, phishing, etc.), severity, affected technology
- [x] New model fields or separate model for AI-generated metadata
- [x] API endpoint to filter by tag: `GET /api/articles/?threat_type=ransomware`
- [x] **New dependency**: `ollama` Python SDK (talks to local Ollama server)

---

## Phase 4: Biplane — Celery + Background Processing ✅

**Goal**: Move feed scraping and LLM calls to background tasks.

- [x] Set up Celery with Redis as the broker
- [x] Periodic task to fetch feeds on a schedule
- [x] Async task for LLM enrichment (summarize, tag, extract)
- [x] Proper error handling and retry logic
- [x] **New dependencies**: `celery`, `redis`

---

## Phase 5: Airplane — IOC & CVE Extraction

**Goal**: Pull indicators of compromise and CVE data out of articles.

- [ ] Extract from article text:
  - [ ] IP addresses, domains, file hashes (MD5, SHA1, SHA256), CVE IDs
- [ ] Start with regex, enhance with LLM for context
- [ ] Cross-reference extracted CVE IDs against local `../cve-search` database for full details (severity, affected products, references)
- [ ] New model: `IOC` linked to source articles
- [ ] API endpoints:
  - [ ] `GET /api/iocs/?type=ip`
  - [ ] `GET /api/cves/?id=CVE-2024-1234` — enriched from local cve-search

---

## Phase 6: Jet — React Dashboard

**Goal**: Build a frontend to browse and search threat intel.

- [ ] React app with filtering and search
- [ ] Views: article list, article detail with IOCs, IOC search
- [ ] Security headers and CORS configuration
- [ ] **Done when**: You can browse, filter, and search articles in the browser

---

## Phase 7: Rocket — RAG + Vector Search ✅

**Goal**: Natural language queries over your threat intel.

- [x] Embed articles into a vector database (ChromaDB to start)
- [x] RAG pipeline: query with natural language, retrieve relevant threats
- [x] API endpoint: `GET /api/search/?q=recent ransomware targeting healthcare`
- [x] **New dependency**: `chromadb` (runs fully local, no cloud account needed)
- [x] Automatic embedding of articles after AI enrichment
- [x] Management command to backfill embeddings: `python manage.py embed_articles`
- [x] **Done when**: You can query articles using natural language and get semantically relevant results

### Usage Examples

```bash
# Search for ransomware articles
curl "http://localhost:8000/api/articles/search/?q=ransomware attacks on healthcare"

# Search with filters
curl "http://localhost:8000/api/articles/search/?q=critical vulnerabilities&severity=critical&limit=5"

# Get vector database statistics
curl "http://localhost:8000/api/articles/vector-stats/"

# Backfill embeddings for existing articles
python manage.py embed_articles --enriched-only

# Embed all articles (including unenriched)
python manage.py embed_articles --limit 100
```

---

## Phase 8: Spaceship — Docker + Deployment

**Goal**: Containerize and orchestrate everything.

- [x] Dockerfiles for Django, React, Celery worker
- [x] Docker Compose to run the full stack locally
- [ ] API versioning
- [ ] Caching strategy with Redis

### Docker Quick Start (One Command)

1. Copy env template and set secrets/passwords:
```bash
cp .env.example .env
```

2. Start full local stack:
```bash
docker compose up --build
```

Services started:
- Django API: `http://localhost:8000`
- React frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6380`
- Celery worker + beat

Notes:
- Django migrations run automatically when `backend` starts.
- Postgres app user/database are initialized automatically on first startup.
- On first run (empty `Article` table), backend auto-runs:
  - `python manage.py fetch_feed`
  - `python manage.py enrich_articles --limit 20` (configurable)
- Ollama is still expected to run separately on the host for AI enrichment.

---

## Best Practices (Applied as We Go)

- [ ] Database migrations and version control
- [ ] Secrets management (environment variables, never hardcoded)
- [ ] Security headers and CORS
- [ ] API versioning
- [ ] Caching strategy
- [ ] Background task management

## Offline-First Prerequisites

Before going offline, make sure you have:
- [ ] `ollama pull mistral` (or whichever model you pick) — downloads the model weights locally
- [ ] `pip install` all dependencies (or use a venv with everything pre-installed)
- [ ] Fetched a batch of articles to have data to work with
- [ ] `../cve-search` populated with latest CVE data
- [ ] PostgreSQL, Redis running locally
