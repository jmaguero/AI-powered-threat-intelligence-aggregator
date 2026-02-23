# Phase 7: RAG + Vector Search Implementation Guide

## Overview

Phase 7 implements Retrieval-Augmented Generation (RAG) using ChromaDB for semantic search over threat intelligence articles. This enables natural language queries like "recent ransomware targeting healthcare" to find relevant articles based on meaning, not just keyword matching.

## Architecture

### Components

1. **ChromaDB**: Local vector database that stores article embeddings
2. **Ollama Embeddings**: Uses the same local LLM to generate embeddings
3. **Vector Store Module** (`feeds/vector_store.py`): Handles all ChromaDB operations
4. **Semantic Search API** (`/api/articles/search/`): REST endpoint for natural language queries
5. **Automatic Indexing**: Articles are embedded automatically after AI enrichment

### Data Flow

```
Article Created → AI Enrichment (Celery Task) → Generate Embedding → Store in ChromaDB
                                                                              ↓
User Query → Generate Query Embedding → Search ChromaDB → Return Matching Articles
```

## Installation

### 1. Install Dependencies

```bash
poetry add chromadb
# or
pip install chromadb
```

### 2. Database Location

ChromaDB data is stored locally at: `./chroma_db/`

This directory is created automatically and persists across restarts. No cloud connection required.

## Usage

### API Endpoints

#### Semantic Search

```bash
GET /api/articles/search/?q=<query>
```

**Query Parameters:**
- `q` (required): Natural language search query
- `limit` (optional): Number of results (default: 10, max: 50)
- `threat_type` (optional): Filter by threat type
- `severity` (optional): Filter by severity level
- `source` (optional): Filter by source

**Examples:**

```bash
# Basic search
curl "http://localhost:8000/api/articles/search/?q=ransomware attacks"

# Search with limit
curl "http://localhost:8000/api/articles/search/?q=phishing campaigns&limit=5"

# Search with filters
curl "http://localhost:8000/api/articles/search/?q=critical vulnerabilities&severity=critical&source=CISA"

# Complex query
curl "http://localhost:8000/api/articles/search/?q=supply chain attacks targeting software vendors"
```

**Response Format:**

```json
{
  "query": "ransomware attacks",
  "count": 5,
  "results": [
    {
      "id": 123,
      "title": "New Ransomware Campaign Targets Healthcare",
      "ai_summary": "...",
      "threat_type": "ransomware",
      "severity": "critical",
      "relevance_score": 0.92,
      ...
    }
  ]
}
```

The `relevance_score` (0-1) indicates how closely the article matches the query.

#### Vector Database Statistics

```bash
GET /api/articles/vector-stats/
```

Returns information about the vector database:

```json
{
  "count": 1234,
  "name": "threat_intel_articles"
}
```

### Management Commands

#### Embed Articles

Use this to backfill embeddings for existing articles or re-index the database.

```bash
# Embed all enriched articles
python manage.py embed_articles --enriched-only

# Embed first 100 articles (useful for testing)
python manage.py embed_articles --limit 100

# Embed all articles (including unenriched)
python manage.py embed_articles

# Force re-embedding of all articles
python manage.py embed_articles --force
```

**Output:**

```
Vector DB before: 0 articles indexed
Filtering to enriched articles only
Processing 150 articles...
Progress: 10/150 (10 success, 0 errors)
Progress: 20/150 (20 success, 0 errors)
...
==================================================
Embedding complete!
Total processed: 150
Successful: 150
Errors: 0
Vector DB after: 150 articles indexed
Net change: +150 articles
```

### Celery Tasks

#### Automatic Embedding

Articles are automatically embedded when enriched:

```python
# This happens automatically in the enrich_article_task
article = Article.objects.get(id=123)
enrich_article_task.delay(article.id)  # Will also embed the article
```

#### Batch Embedding

For periodic maintenance or bulk operations:

```python
from feeds.tasks import embed_articles_batch

# Embed up to 50 enriched articles
embed_articles_batch.delay(limit=50, enriched_only=True)
```

## How It Works

### Embedding Generation

Each article is converted to text combining:
- Title
- Summary
- AI-generated summary
- Threat type
- Severity
- Affected technology
- Source

This text is sent to Ollama to generate a dense vector representation (embedding).

### Semantic Search

1. User query is embedded using the same model
2. ChromaDB finds articles with similar embeddings (cosine similarity)
3. Results are ranked by relevance
4. Optional filters (threat_type, severity, source) are applied
5. Full article data is fetched from PostgreSQL
6. Results include relevance scores

### Why This Works

Unlike keyword search, semantic search understands:
- **Synonyms**: "malware" matches "malicious software"
- **Context**: "targeting hospitals" matches "healthcare sector"
- **Concepts**: "supply chain compromise" matches "third-party vendor attack"

## Best Practices

### 1. Enrich Before Embedding

Always enrich articles with AI metadata before embedding. Enriched articles produce better embeddings because they include:
- Standardized threat types
- Severity assessments
- Extracted technology names

```bash
# Good workflow
python manage.py fetch_feed
python manage.py enrich_articles  # Automatically embeds
```

### 2. Query Design

**Good queries** are specific but not overly technical:
- ✅ "ransomware attacks on healthcare providers"
- ✅ "critical vulnerabilities in Microsoft products"
- ✅ "phishing campaigns targeting financial institutions"

**Less effective queries**:
- ❌ "CVE-2024-1234" (use regular search for exact matches)
- ❌ "bad stuff" (too vague)
- ❌ Single words like "malware" (add context)

### 3. Combining with Filters

Use semantic search for the query, filters for metadata:

```bash
# Find ransomware articles, but only critical severity
curl "http://localhost:8000/api/articles/search/?q=ransomware campaigns&severity=critical"
```

### 4. Re-indexing

Re-embed articles when:
- You change the embedding model
- You significantly update article enrichment
- You suspect stale embeddings

```bash
python manage.py embed_articles --force
```

## Troubleshooting

### "Command not found: chromadb"

ChromaDB is a library, not a command. Use it through Django:

```bash
python manage.py embed_articles
```

### "Failed to generate embedding: Connection refused"

Ollama is not running. Start it:

```bash
ollama serve
```

### "No results for query"

Possible causes:
1. No articles have been embedded yet
   - Solution: Run `python manage.py embed_articles`

2. Query is too specific or uses exact technical terms
   - Solution: Try broader queries

3. Filters are too restrictive
   - Solution: Remove filters or broaden them

### Check Vector DB Status

```bash
curl http://localhost:8000/api/articles/vector-stats/
```

If count is 0, run the embed command.

### Embedding Errors

If articles fail to embed:
1. Check Ollama is running: `ollama list`
2. Check model is available: `ollama pull qwen2.5:7b`
3. Check article has content (not just empty fields)
4. Check ChromaDB directory permissions: `ls -la ./chroma_db/`

## Performance Considerations

### Embedding Speed

- Embedding generation: ~1-2 seconds per article (depends on model)
- For 1000 articles: ~20-30 minutes
- Use Celery tasks for background processing

### Search Speed

- Query embedding: ~1-2 seconds
- Vector search: <100ms (even with thousands of articles)
- Total response time: ~1-2 seconds

### Storage

- Embeddings: ~4KB per article (for 1024-dimensional vectors)
- 10,000 articles ≈ 40MB
- ChromaDB is efficient and indexes automatically

## Advanced Usage

### Custom Embedding Models

To use a different Ollama model for embeddings:

```python
# In feeds/vector_store.py, update the default model
def generate_embedding(text: str, model: str = "nomic-embed-text") -> list[float]:
    ...
```

**Recommended models:**
- `nomic-embed-text`: Optimized for embeddings, smaller, faster
- `qwen2.5:7b`: What we use now, good balance
- `llama3`: Larger, more accurate, slower

### Batch Processing Schedule

Add to Celery beat for periodic embedding:

```python
# In threatintel/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'embed-new-articles': {
        'task': 'feeds.tasks.embed_articles_batch',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': (100, True),  # Limit 100, enriched only
    },
}
```

### Hybrid Search

Combine semantic search with traditional filtering:

```python
# Get semantic matches
semantic_ids = semantic_search(query, n_results=100)

# Apply additional business logic
articles = Article.objects.filter(
    id__in=semantic_ids,
    published_date__gte=last_week,
    severity__in=['critical', 'high']
).exclude(
    threat_type='informational'
)
```

## Testing

### Quick Test

1. Ensure Ollama is running
2. Create/fetch some articles
3. Enrich them
4. Try a search:

```bash
# Fetch articles
python manage.py fetch_feed

# Enrich (also embeds)
python manage.py enrich_articles --limit 10

# Search
curl "http://localhost:8000/api/articles/search/?q=security vulnerabilities"
```

### Verify Embeddings

```bash
# Check vector DB has articles
curl http://localhost:8000/api/articles/vector-stats/

# Should return: {"count": 10, "name": "threat_intel_articles"}
```

## Next Steps

With Phase 7 complete, you now have:
- ✅ Multi-source threat intel aggregation
- ✅ AI-powered enrichment and classification
- ✅ Background processing with Celery
- ✅ Semantic search with RAG

**Ready for Phase 8**: Docker + Deployment
- Containerize the entire stack
- Add caching layers
- Implement API versioning
- Set up Kubernetes orchestration

## Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Ollama Embeddings](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings)
- [RAG Explained](https://www.promptingguide.ai/techniques/rag)
