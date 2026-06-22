#!/bin/sh
set -e

echo "Running edge-api migrations..."
alembic upgrade head
echo "Migrations done."

exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
