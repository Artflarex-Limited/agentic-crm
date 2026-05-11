#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

echo "==> Running database migrations"

docker-compose -f "$COMPOSE_FILE" run --rm backend bash -c "
    echo 'Running Alembic migrations...'
    alembic upgrade head
    echo 'Migrations complete'
"

echo "==> Migration complete"