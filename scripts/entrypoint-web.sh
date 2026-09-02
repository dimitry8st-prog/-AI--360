#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting web..."
exec uvicorn app.main:app --host "${WEB_HOST:-0.0.0.0}" --port "${WEB_PORT:-8000}"
