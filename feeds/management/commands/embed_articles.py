"""
Management command to embed articles into the vector database.

Usage:
    python manage.py embed_articles           # Embed all articles
    python manage.py embed_articles --limit 10  # Embed first 10 articles
    python manage.py embed_articles --enriched-only  # Only embed enriched articles
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from feeds.models import Article
from feeds.vector_store import add_article_to_vector_db, get_vector_db_stats


class Command(BaseCommand):
    help = "Embed articles into the vector database for semantic search"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of articles to embed"
        )
        parser.add_argument(
            "--enriched-only",
            action="store_true",
            help="Only embed articles that have been enriched with AI metadata"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-embed all articles even if they might already be in the vector DB"
        )

    def handle(self, *args, **options):
        # Get vector DB stats before
        stats_before = get_vector_db_stats()
        self.stdout.write(
            f"Vector DB before: {stats_before['count']} articles indexed"
        )

        # Build queryset
        queryset = Article.objects.all()

        if options["enriched_only"]:
            queryset = queryset.filter(enriched_at__isnull=False)
            self.stdout.write("Filtering to enriched articles only")

        if options["limit"]:
            queryset = queryset[:options["limit"]]
            self.stdout.write(f"Limiting to {options['limit']} articles")

        # Embed articles
        total = queryset.count()
        success_count = 0
        error_count = 0

        self.stdout.write(f"Processing {total} articles...")

        for i, article in enumerate(queryset, 1):
            try:
                success = add_article_to_vector_db(article)
                if success:
                    success_count += 1
                else:
                    error_count += 1

                # Progress indicator every 10 articles
                if i % 10 == 0:
                    self.stdout.write(
                        f"Progress: {i}/{total} ({success_count} success, {error_count} errors)"
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error embedding article {article.id}: {e}")
                )

        # Get vector DB stats after
        stats_after = get_vector_db_stats()

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Embedding complete!"))
        self.stdout.write(f"Total processed: {total}")
        self.stdout.write(f"Successful: {success_count}")
        self.stdout.write(f"Errors: {error_count}")
        self.stdout.write(f"Vector DB after: {stats_after['count']} articles indexed")
        self.stdout.write(
            f"Net change: +{stats_after['count'] - stats_before['count']} articles"
        )
