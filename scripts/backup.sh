#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="agentic_crm_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

mkdir -p "$BACKUP_DIR"

COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

echo "==> Creating backup: $BACKUP_NAME"

docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U agentic_user agentic_crm | gzip > "$BACKUP_PATH"

BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
echo "==> Backup created: $BACKUP_PATH ($BACKUP_SIZE)"

if [ -n "$AWS_S3_BUCKET" ]; then
    echo "==> Uploading to S3: s3://${AWS_S3_BUCKET}/${BACKUP_NAME}"
    aws s3 cp "$BACKUP_PATH" "s3://${AWS_S3_BUCKET}/${BACKUP_NAME}"
    echo "==> S3 upload complete"
fi

echo "==> Cleaning old backups (keeping last 7)"
cd "$BACKUP_DIR" && ls -t | tail -n +8 | xargs -r rm

echo "==> Backup complete"
ls -lh "$BACKUP_DIR"