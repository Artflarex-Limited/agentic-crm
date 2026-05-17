#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR/backend"

echo "=== Running Alembic migrations ==="

if [ -n "$POSTGRES_PASSWORD" ]; then
    export PGPASSWORD="$POSTGRES_PASSWORD"
fi

DATABASE_URL="${DATABASE_URL:-postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-agentic_crm}}"

export DATABASE_URL

if ! command -v alembic &> /dev/null; then
    echo "Alembic not found, installing..."
    pip install alembic
fi

alembic upgrade head

echo "=== Migrations complete ==="