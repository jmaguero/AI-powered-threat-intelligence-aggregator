# Phase 7 Quick Start Guide

## What's New?

Phase 7 adds **semantic search** to your threat intelligence platform. Instead of searching for exact keywords, you can now ask questions in natural language:

- "What are recent ransomware attacks on healthcare?"
- "Critical vulnerabilities in Microsoft products"
- "Supply chain compromises targeting software vendors"

The system understands meaning, not just keywords!

## Prerequisites

1. **Ollama running** with a model pulled:
   ```bash
   ollama serve
   ollama pull qwen2.5:7b
   ```

2. **Phase 1-4 completed**: Articles fetched and enriched
   ```bash
   python manage.py fetch_feed
   python manage.py enrich_articles
   ```

## Installation (One-Time Setup)

### 1. Install ChromaDB

```bash
poetry add chromadb
# or
pip install chromadb
```

### 2. Run Migrations (if needed)

```bash
python manage.py migrate
```

### 3. Embed Existing Articles

```bash
# Embed all enriched articles
python manage.py embed_articles --enriched-only
```

This will take a few minutes depending on how many articles you have. Watch the progress output!

## Usage

### Start the Server

```bash
python manage.py runserver
```

### Test Semantic Search

```bash
# Basic search
curl "http://localhost:8000/api/articles/search/?q=ransomware"

# Search with filters
curl "http://localhost:8000/api/articles/search/?q=vulnerabilities&severity=critical&limit=5"

# Check vector DB status
curl "http://localhost:8000/api/articles/vector-stats/"
```

### Run the Test Suite

```bash
python test_semantic_search.py
```

Expected output:
```
============================================================
  Phase 7: Semantic Search Test Suite
============================================================

Testing Vector Database Statistics
✓ Vector DB Stats Retrieved
  Articles indexed: 150

Testing Semantic Search: 'ransomware attacks'
✓ Search completed
  Results found: 12
  Top 3 results:
  1. [0.89] New Ransomware Campaign Targets Healthcare Sector
     Threat: ransomware | Severity: critical | Source: CISA
  ...
```

## Automatic Background Processing

Once set up, articles are **automatically embedded** when enriched by Celery:

```
New Article → fetch_feed task → enrich_article_task → embed into vector DB
```

No manual intervention needed!

## Common Queries to Try

```bash
# Find specific threats
curl "http://localhost:8000/api/articles/search/?q=phishing campaigns"

# Find by affected tech
curl "http://localhost:8000/api/articles/search/?q=attacks on Apache servers"

# Find by industry
curl "http://localhost:8000/api/articles/search/?q=threats to financial institutions"

# Complex queries
curl "http://localhost:8000/api/articles/search/?q=supply chain attacks using malicious npm packages"
```

## Troubleshooting

### No Results?

1. **Check vector DB has articles:**
   ```bash
   curl http://localhost:8000/api/articles/vector-stats/
   ```
   If `count: 0`, run: `python manage.py embed_articles`

2. **Check Ollama is running:**
   ```bash
   ollama list
   ```
   Should show `qwen2.5:7b` or your model

3. **Try broader queries:**
   - Instead of: "CVE-2024-1234" (too specific)
   - Try: "vulnerabilities in web servers"

### Slow Searches?

- First search is slow (generates query embedding): ~1-2 seconds
- Subsequent searches are fast: <100ms
- This is normal!

### Embedding Errors?

```bash
# Check Django logs
python manage.py runserver

# Check Celery logs
celery -A threatintel worker --loglevel=info
```

## What Happens Behind the Scenes?

1. **Article text is combined:**
   - Title + Summary + AI Summary + Metadata

2. **Sent to Ollama for embedding:**
   - Creates a vector (list of numbers) representing the meaning

3. **Stored in ChromaDB:**
   - Local database at `./chroma_db/`
   - No cloud, all offline

4. **Query is embedded the same way:**
   - Your question → vector

5. **ChromaDB finds similar vectors:**
   - Uses cosine similarity
   - Returns most relevant articles

## File Structure

Phase 7 adds these files:

```
feeds/
├── vector_store.py          # ChromaDB operations
├── views.py                 # Added SemanticSearchView
├── tasks.py                 # Updated to embed articles
└── management/commands/
    └── embed_articles.py    # Backfill command

chroma_db/                   # Vector database (auto-created)
test_semantic_search.py      # Test script
PHASE7_RAG_GUIDE.md         # Detailed documentation
PHASE7_QUICKSTART.md        # This file
```

## API Reference

### Semantic Search Endpoint

```
GET /api/articles/search/
```

**Parameters:**
- `q` (required): Search query
- `limit` (optional): Max results (default: 10, max: 50)
- `threat_type` (optional): Filter by threat type
- `severity` (optional): Filter by severity
- `source` (optional): Filter by source

**Response:**
```json
{
  "query": "ransomware",
  "count": 5,
  "results": [
    {
      "id": 123,
      "title": "...",
      "relevance_score": 0.89,
      ...
    }
  ]
}
```

### Vector DB Stats Endpoint

```
GET /api/articles/vector-stats/
```

**Response:**
```json
{
  "count": 150,
  "name": "threat_intel_articles"
}
```

## Next Steps

1. **Integrate into frontend** (Phase 6)
   - Add search bar to React app
   - Display relevance scores
   - Show "Similar articles" feature

2. **Periodic re-indexing** (Celery beat)
   - Schedule daily embedding batches
   - Keep vector DB in sync

3. **Advanced RAG** (Optional)
   - Try different embedding models
   - Implement hybrid search (keyword + semantic)
   - Add query expansion

## Full Documentation

For detailed information, see:
- **PHASE7_RAG_GUIDE.md**: Complete implementation guide
- **README.md**: Project overview and all phases

## Support

Issues? Check:
1. Ollama is running: `ollama serve`
2. Django is running: `python manage.py runserver`
3. Articles are embedded: `curl http://localhost:8000/api/articles/vector-stats/`
4. Celery is running (for auto-embedding): `celery -A threatintel worker`

---

**Phase 7 Complete!** 🚀

You now have a fully functional RAG-powered threat intelligence platform with semantic search capabilities!
