from celery import shared_task
from django.db.models import Q
from datetime import datetime, timezone

from feeds.models import Article, IOC
from feeds.ai_enrichment import enrich_article
from feeds.management.commands.fetch_feed import FEED_SOURCES
from feeds.vector_store import add_article_to_vector_db
from feeds.ioc_extraction import extract_iocs_from_text
import feedparser


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
)
def fetch_feed(self, source_name, feed_url):
    """
    Fetch articles from a single RSS feed source.

    Args:
        source_name: Name of the source (e.g., "CISA", "Krebs")
        feed_url: URL of the RSS feed

    Returns:
        Number of new articles created
    """
    try:
        feed = feedparser.parse(feed_url)
        created_count = 0

        for entry in feed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            _, created = Article.objects.get_or_create(
                link=entry.link,
                defaults={
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "published_date": published,
                    "source": source_name,
                },
            )
            if created:
                created_count += 1
                # Trigger enrichment for new article
                enrich_article_task.delay(Article.objects.get(link=entry.link).id)

        return created_count
    except Exception as e:
        raise self.retry(exc=e)


@shared_task
def fetch_all_feeds():
    """
    Fetch articles from all configured RSS feeds.

    Returns:
        dict with source names and article counts
    """
    results = {}

    for source_name, feed_url in FEED_SOURCES.items():
        result = fetch_feed.delay(source_name, feed_url)
        results[source_name] = f"Task {result.id} queued"

    return results


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 120},
    retry_backoff=True,
)
def enrich_article_task(self, article_id):
    """
    Enrich a single article with AI-generated metadata.

    Args:
        article_id: Primary key of the Article to enrich

    Returns:
        dict with enrichment results
    """
    try:
        article = Article.objects.get(id=article_id)

        # Skip if already enriched recently (within 24 hours)
        if article.enriched_at:
            hours_since_enrichment = (datetime.now(timezone.utc) - article.enriched_at).total_seconds() / 3600
            if hours_since_enrichment < 24:
                return {"status": "skipped", "reason": "recently enriched"}

        # 1. AI enrichment
        enrichment_data = enrich_article(article, model="qwen2.5:7b")

        # 2. Extract IOCs from article text
        full_text = f"{article.title}\n\n{article.summary}"
        extracted_iocs = extract_iocs_from_text(full_text, article_id=article.id)

        # 3. Save enrichment data
        for field, value in enrichment_data.items():
            setattr(article, field, value)
        article.save()

        # 4. Create/update IOC records and link to article
        ioc_count = 0
        for ioc_data in extracted_iocs:
            ioc, created = IOC.objects.get_or_create(
                value=ioc_data['value'],
                ioc_type=ioc_data['type'],
                defaults={
                    'confidence': ioc_data.get('confidence', 'medium'),
                    'context': ioc_data.get('context', '')[:500],  # Limit context length
                }
            )

            if not created:
                # Update existing IOC metadata
                ioc.last_seen = datetime.now(timezone.utc)
                ioc.times_seen += 1
                ioc.save()

            # Link to article (ManyToMany) - idempotent operation
            if not article.iocs.filter(id=ioc.id).exists():
                article.iocs.add(ioc)
                ioc_count += 1

        # 5. Add to vector database for semantic search
        vector_db_success = add_article_to_vector_db(article)

        return {
            "status": "success",
            "article_id": article_id,
            "threat_type": article.threat_type,
            "severity": article.severity,
            "iocs_extracted": ioc_count,
            "total_iocs": len(extracted_iocs),
            "vector_db_indexed": vector_db_success,
        }
    except Article.DoesNotExist:
        return {"status": "error", "reason": "article not found"}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task
def enrich_unenriched_articles(limit=50):
    """
    Enrich articles that haven't been analyzed yet.

    Args:
        limit: Maximum number of articles to enrich in this batch

    Returns:
        Number of enrichment tasks queued
    """
    articles = Article.objects.filter(
        Q(enriched_at__isnull=True) | Q(ai_summary="")
    )[:limit]

    count = 0
    for article in articles:
        enrich_article_task.delay(article.id)
        count += 1

    return {"queued": count, "limit": limit}


@shared_task
def embed_articles_batch(limit=50, enriched_only=True):
    """
    Embed a batch of articles into the vector database.

    Args:
        limit: Maximum number of articles to embed in this batch
        enriched_only: Only embed articles that have been enriched

    Returns:
        dict with success and error counts
    """
    queryset = Article.objects.all()

    if enriched_only:
        queryset = queryset.filter(enriched_at__isnull=False)

    articles = queryset[:limit]

    success_count = 0
    error_count = 0

    for article in articles:
        try:
            if add_article_to_vector_db(article):
                success_count += 1
            else:
                error_count += 1
        except Exception:
            error_count += 1

    return {
        "total": success_count + error_count,
        "success": success_count,
        "errors": error_count,
    }
