#!/bin/bash
set -e

# Закомментируйте эти строки:
# echo "Running database migrations..."
# alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload