from django.core.management.base import BaseCommand
from django.db.models import Q

from feeds.models import Article
from feeds.ai_enrichment import enrich_article


class Command(BaseCommand):
    help = "Enrich articles with AI-generated summaries and tags using Ollama"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of articles to enrich (default: 10)",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="qwen2.5:7b",
            help="Ollama model to use (default: qwen2.5:7b)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Enrich all unenriched articles (ignores --limit)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-enrich articles even if already enriched",
        )

    def handle(self, *args, **options):
        model = options["model"]
        limit = options["limit"]
        enrich_all = options["all"]
        force = options["force"]

        # Query articles
        if force:
            articles = Article.objects.all()
        else:
            articles = Article.objects.filter(
                Q(enriched_at__isnull=True) | Q(ai_summary="")
            )

        if not enrich_all:
            articles = articles[:limit]

        total = articles.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No articles to enrich"))
            return

        self.stdout.write(f"Enriching {total} articles with model: {model}")

        success_count = 0
        error_count = 0

        for idx, article in enumerate(articles, 1):
            self.stdout.write(f"[{idx}/{total}] Processing: {article.title[:60]}...")

            try:
                enrichment_data = enrich_article(article, model=model)

                # Update article fields
                for field, value in enrichment_data.items():
                    setattr(article, field, value)
                article.save()

                self.stdout.write(
                    f"  ✓ Type: {article.threat_type}, Severity: {article.severity}"
                )
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {success_count} enriched, {error_count} errors"
            )
        )
