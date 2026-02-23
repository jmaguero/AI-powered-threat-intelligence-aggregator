#!/bin/bash
# Run Celery worker and beat scheduler

# Start Celery worker
poetry run celery -A threatintel worker --loglevel=info --concurrency=4 &
WORKER_PID=$!

# Start Celery beat scheduler (for periodic tasks)
poetry run celery -A threatintel beat --loglevel=info &
BEAT_PID=$!

echo "Celery worker PID: $WORKER_PID"
echo "Celery beat PID: $BEAT_PID"
echo "Press Ctrl+C to stop..."

# Wait for Ctrl+C
trap "kill $WORKER_PID $BEAT_PID 2>/dev/null; exit" INT TERM

wait
