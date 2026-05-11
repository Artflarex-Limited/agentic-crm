#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

echo "==> Seeding database with sample data"

docker-compose -f "$COMPOSE_FILE" run --rm backend bash -c "
    echo 'Running database seed...'
    python -m app.seed || echo 'No seed module found, skipping'
"

echo "==> Seed complete"