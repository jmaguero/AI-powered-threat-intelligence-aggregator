# Phase 5: IOC & CVE Extraction - Implementation Summary

## ✅ Completed Tasks

### 1. Database Model (feeds/models.py)
- Added `IOC` model with fields:
  - `value`: The IOC value (IP, domain, hash, CVE, etc.)
  - `ioc_type`: Type of IOC (ip, domain, url, md5, sha1, sha256, cve, email)
  - `confidence`: Confidence level (high, medium, low)
  - `context`: Surrounding text from article
  - `articles`: ManyToMany relationship to Article
  - `first_seen`, `last_seen`, `times_seen`: Tracking metadata
  - `is_validated`, `is_false_positive`: Quality flags
- Added indexes for performance
- Registered IOC in admin interface

### 2. IOC Extraction Module (feeds/ioc_extraction.py)
- Implemented regex patterns for:
  - IPv4 addresses (with private IP filtering)
  - Domains (with false positive filtering)
  - URLs
  - MD5, SHA1, SHA256 hashes
  - CVE identifiers
  - Email addresses
- Defanging logic to normalize obfuscated IOCs:
  - `192[.]168[.]1[.]1` → `192.168.1.1`
  - `hxxp://evil.com` → `http://evil.com`
- Validation functions to filter false positives
- Context extraction for each IOC

### 3. CVE Lookup Integration (feeds/cve_lookup.py)
- MongoDB connection to cve-search database
- `lookup_cve()` function to fetch CVE details:
  - Summary, CVSS scores, severity
  - References, vulnerable products
  - Published/modified dates
- `bulk_lookup_cves()` for efficient batch queries
- Graceful fallback if cve-search unavailable

### 4. Enhanced Celery Task (feeds/tasks.py)
- Modified `enrich_article_task` to:
  1. Perform AI enrichment (existing)
  2. Extract IOCs from article text
  3. Save enrichment data
  4. Create/update IOC records
  5. Link IOCs to articles (ManyToMany)
  6. Index in vector database (existing)
- Returns `iocs_extracted` count in task result

### 5. API Layer
- **Serializers** (feeds/serializers.py):
  - `IOCSerializer`: IOC data with article count/IDs
  - `CVEDetailSerializer`: CVE details from cve-search
  - Updated `ArticleSerializer` to include `ioc_count`

- **Filters** (feeds/filters.py):
  - `IOCFilter`: Filter by type, value, confidence, dates, validation status

- **Views** (feeds/views.py):
  - `IOCListView`: List IOCs with filtering
  - `IOCDetailView`: Get specific IOC with related articles
  - `cve_detail_view`: Lookup CVE from cve-search + our tracking data

- **URLs** (feeds/urls.py):
  - `GET /api/articles/iocs/` - List IOCs
  - `GET /api/articles/iocs/<id>/` - IOC details
  - `GET /api/articles/cves/<cve_id>/` - CVE lookup

### 6. Dependencies
- Added `pymongo` to pyproject.toml for cve-search integration

## 📋 API Endpoints

### List IOCs
```bash
curl "http://localhost:8000/api/articles/iocs/"

# With filtering
curl "http://localhost:8000/api/articles/iocs/?ioc_type=ip"
curl "http://localhost:8000/api/articles/iocs/?ioc_type=cve&confidence=high"
curl "http://localhost:8000/api/articles/iocs/?min_times_seen=5"
```

### Get IOC Details
```bash
curl "http://localhost:8000/api/articles/iocs/1/"
```

### Lookup CVE
```bash
# Requires cve-search MongoDB running
curl "http://localhost:8000/api/articles/cves/CVE-2021-44228/"
```

### List Articles (now includes IOC count)
```bash
curl "http://localhost:8000/api/articles/"
```

## 🧪 Testing

### Test IOC Extraction
```bash
poetry run python manage.py shell << 'EOF'
from feeds.ioc_extraction import extract_iocs_from_text

text = """
CVE-2024-1234 exploited by attackers at 8.8.8.8
Malicious domain: evil-site.com
Hash: abc123def456789012345678901234567890
"""

iocs = extract_iocs_from_text(text)
for ioc in iocs:
    print(f"{ioc['type']}: {ioc['value']} ({ioc['confidence']})")
EOF
```

### Test Full Enrichment Flow
```bash
poetry run python manage.py shell << 'EOF'
from feeds.models import Article
from feeds.tasks import enrich_article_task

# Create article with IOCs
article = Article.objects.create(
    title="CVE-2024-9999: Critical vulnerability",
    summary="Exploited from IP 203.0.113.42 via malicious.example.org",
    link="http://test.com/cve-test-2",
    source="TEST"
)

# Trigger enrichment (extracts IOCs)
result = enrich_article_task(article.id)
print(f"Enriched: {result}")
print(f"Article has {article.iocs.count()} IOCs")

# Show extracted IOCs
for ioc in article.iocs.all():
    print(f"  - {ioc}")
EOF
```

### Test CVE Lookup (requires cve-search)
```bash
# First, ensure cve-search MongoDB is running
# Default connection: mongodb://localhost:27017/cvedb

poetry run python manage.py shell << 'EOF'
from feeds.cve_lookup import test_connection, lookup_cve

# Test connection
if test_connection():
    print("✓ Connected to cve-search")

    # Lookup a well-known CVE
    cve = lookup_cve("CVE-2021-44228")  # Log4Shell
    if cve:
        print(f"\nCVE: {cve['id']}")
        print(f"Summary: {cve['summary'][:100]}...")
        print(f"Severity: {cve.get('severity', 'N/A')}")
        print(f"CVSS: {cve.get('cvss_v3', cve.get('cvss', 'N/A'))}")
else:
    print("✗ cve-search not available")
EOF
```

## 🔄 Workflow

1. **Feed Fetch**: Articles fetched from RSS feeds
2. **Enrichment Task**:
   - AI analyzes article (threat type, severity, etc.)
   - IOCs extracted via regex + validation
   - IOCs saved to database and linked to article
   - Article indexed in vector DB
3. **API Query**:
   - Search/filter articles with IOC counts
   - List/filter IOCs by type, confidence, etc.
   - Lookup CVE details from cve-search

## 📊 Database Schema

```
Article (1) ←→ (M) IOC
  - Articles can have multiple IOCs
  - Same IOC can appear in multiple articles
  - Track first_seen, last_seen, times_seen
```

## 🔍 IOC Types Supported

- **IP Address**: Public IPv4 (private ranges excluded)
- **Domain**: Valid domains (example.com excluded)
- **URL**: Full HTTP/HTTPS URLs
- **MD5**: 32 hex characters
- **SHA1**: 40 hex characters
- **SHA256**: 64 hex characters
- **CVE**: CVE-YYYY-NNNN format (1999-2027)
- **Email**: Standard email addresses

## ⚙️ Configuration

### Settings (threatintel/settings.py)
```python
# CVE-Search MongoDB connection
CVE_SEARCH_MONGO_URI = os.getenv("CVE_SEARCH_MONGO_URI", "mongodb://localhost:27017/")
CVE_SEARCH_DB_NAME = os.getenv("CVE_SEARCH_DB_NAME", "cvedb")
```

### Environment Variables (optional)
```bash
export CVE_SEARCH_MONGO_URI="mongodb://localhost:27017/"
export CVE_SEARCH_DB_NAME="cvedb"
```

## 🚀 Next Steps

1. **Install cve-search** (optional but recommended):
   ```bash
   git clone https://github.com/cve-search/cve-search.git
   cd cve-search
   pip install -r requirements.txt
   ./sbin/db_mgmt.py -p  # Populate database
   ```

2. **Enrich existing articles**:
   ```bash
   poetry run python manage.py run_tasks --enrich --limit 100
   ```

3. **Monitor IOC extraction**:
   - Check admin interface: http://localhost:8000/admin/feeds/ioc/
   - Query API: http://localhost:8000/api/articles/iocs/

4. **Configure false positive filters** if needed:
   - Edit `feeds/ioc_extraction.py`
   - Add domains to `DOMAIN_BLOCKLIST`
   - Adjust regex patterns

## ✨ Features

- ✅ Automatic IOC extraction from threat intelligence
- ✅ Deduplication across articles
- ✅ Tracking metadata (first/last seen, frequency)
- ✅ Confidence scoring
- ✅ CVE enrichment from cve-search
- ✅ Filterable REST API
- ✅ Admin interface for management
- ✅ Graceful degradation (works without cve-search)
