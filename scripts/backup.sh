#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/tmp/backups}"
S3_BUCKET="${S3_BUCKET:-}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-agentic_crm}"

if [ -n "$POSTGRES_PASSWORD" ]; then
    export PGPASSWORD="$POSTGRES_PASSWORD"
fi

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="agentic_crm_${TIMESTAMP}.sql.gz"

echo "=== Starting PostgreSQL backup ==="
echo "Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "Database: $POSTGRES_DB"
echo "Backup file: $BACKUP_FILE"

pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

echo "Backup created: $BACKUP_DIR/$BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"

if [ -n "$S3_BUCKET" ]; then
    echo "Uploading to S3: s3://$S3_BUCKET/backups/$BACKUP_FILE"

    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://$S3_BUCKET/backups/$BACKUP_FILE"
        echo "Upload complete"
    else
        echo "AWS CLI not found, skipping S3 upload"
    fi
fi

find "$BACKUP_DIR" -name "agentic_crm_*.sql.gz" -mtime +7 -delete
echo "Cleaned up backups older than 7 days"

echo "=== Backup complete ==="