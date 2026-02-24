FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY --chown=appuser:appuser pyproject.toml poetry.lock* /app/
RUN poetry install --no-root

COPY --chown=appuser:appuser . /app
RUN chmod +x /app/docker/backend/entrypoint.sh

USER appuser

ENTRYPOINT ["/app/docker/backend/entrypoint.sh"]
