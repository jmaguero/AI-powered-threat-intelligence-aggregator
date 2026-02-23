from datetime import datetime, timezone

import feedparser
from django.core.management.base import BaseCommand

from feeds.models import Article

FEED_SOURCES = {
    "CISA": "https://www.cisa.gov/news.xml",
    "Krebs": "https://krebsonsecurity.com/feed/",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "US-CERT": "https://www.cisa.gov/uscert/ncas/current-activity.xml",
}


class Command(BaseCommand):
    help = "Fetch articles from multiple threat intelligence RSS feeds"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            help=f"Fetch from a specific source: {', '.join(FEED_SOURCES.keys())}",
        )

    def handle(self, *args, **options):
        sources_to_fetch = FEED_SOURCES
        if options.get("source"):
            source_name = options["source"]
            if source_name not in FEED_SOURCES:
                self.stdout.write(self.style.ERROR(f"Unknown source: {source_name}"))
                return
            sources_to_fetch = {source_name: FEED_SOURCES[source_name]}

        total_created = 0
        total_entries = 0

        for source_name, feed_url in sources_to_fetch.items():
            self.stdout.write(f"Fetching from {source_name}...")
            created_count = self._fetch_feed(source_name, feed_url)
            total_created += created_count

        self.stdout.write(
            self.style.SUCCESS(f"Fetched {total_created} new articles from {len(sources_to_fetch)} sources")
        )

    def _fetch_feed(self, source_name, feed_url):
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

            self.stdout.write(f"  {source_name}: {created_count} new articles ({len(feed.entries)} total in feed)")
            return created_count
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  {source_name}: Error - {e}"))
            return 0
