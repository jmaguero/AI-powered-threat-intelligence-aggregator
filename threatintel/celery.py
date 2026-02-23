import os

from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'threatintel.settings')

app = Celery('threatintel')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in installed apps
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    'fetch-feeds-every-hour': {
        'task': 'feeds.tasks.fetch_all_feeds',
        'schedule': crontab(minute=0),  # Every hour
    },
    'enrich-articles-every-2-hours': {
        'task': 'feeds.tasks.enrich_unenriched_articles',
        'schedule': crontab(minute=30, hour='*/2'),  # Every 2 hours at :30
    },
}
