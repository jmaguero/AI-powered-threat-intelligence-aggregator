from django.core.management.base import BaseCommand

from feeds.tasks import fetch_all_feeds, enrich_unenriched_articles


class Command(BaseCommand):
    help = "Manually trigger background tasks (requires Celery worker to be running)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fetch",
            action="store_true",
            help="Trigger feed fetch tasks",
        )
        parser.add_argument(
            "--enrich",
            action="store_true",
            help="Trigger article enrichment tasks",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Limit for enrichment tasks (default: 50)",
        )

    def handle(self, *args, **options):
        if not options["fetch"] and not options["enrich"]:
            self.stdout.write(self.style.ERROR("Specify --fetch or --enrich"))
            return

        if options["fetch"]:
            self.stdout.write("Triggering feed fetch tasks...")
            result = fetch_all_feeds.delay()
            self.stdout.write(self.style.SUCCESS(f"Task queued: {result.id}"))

        if options["enrich"]:
            limit = options["limit"]
            self.stdout.write(f"Triggering enrichment tasks (limit: {limit})...")
            result = enrich_unenriched_articles.delay(limit=limit)
            self.stdout.write(self.style.SUCCESS(f"Task queued: {result.id}"))

        self.stdout.write(
            "\nNote: Tasks are queued. Make sure Celery worker is running with:"
        )
        self.stdout.write("  ./run_celery.sh")
        self.stdout.write("  or: poetry run celery -A threatintel worker --loglevel=info")
