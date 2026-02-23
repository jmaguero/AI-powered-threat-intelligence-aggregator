#!/bin/sh
set -e

if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
  echo "Applying migrations..."
  poetry run python manage.py migrate --noinput

  if [ "${AUTO_BOOTSTRAP_FEEDS:-1}" = "1" ]; then
    ARTICLE_COUNT=$(poetry run python manage.py shell -c "from feeds.models import Article; print(Article.objects.count())" | tail -n 1)
    if [ "$ARTICLE_COUNT" = "0" ]; then
      echo "No articles found. Running initial fetch + enrichment bootstrap..."
      poetry run python manage.py fetch_feed
      poetry run python manage.py enrich_articles --limit "${BOOTSTRAP_ENRICH_LIMIT:-20}"
    else
      echo "Articles already present ($ARTICLE_COUNT). Skipping bootstrap."
    fi
  fi
fi

exec "$@"
