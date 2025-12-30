#!/usr/bin/env bash
# Entrypoint script for running payvest Flask app with Gunicorn in production

set -e

# Default: listen on 0.0.0.0:8000, 4 workers, use uvicorn worker for async support
HOST="0.0.0.0"
PORT="8000"
WORKERS="4"
APP_MODULE="app:create_app()"

exec gunicorn \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --worker-class "gthread" \
    --timeout 120 \
    --log-level info \
    --access-logfile "-" \
    --error-logfile "-" \
    --capture-output \
    --enable-stdio-inheritance \
    --preload \
    --factory "${APP_MODULE}"
