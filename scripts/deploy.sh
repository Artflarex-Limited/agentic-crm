#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

TAG="${1:-latest}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

echo "==> Deploying Agentic CRM (tag: $TAG)"

export TAG="$TAG"

echo "==> Pulling latest images"
docker-compose -f "$COMPOSE_FILE" pull

echo "==> Building custom images with tag"
docker-compose -f "$COMPOSE_FILE" build --build-arg BUILDKIT_INLINE_CACHE=1

echo "==> Starting services"
docker-compose -f "$COMPOSE_FILE" up -d

echo "==> Waiting for backend health"
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is healthy"
        break
    fi
    echo "Waiting for backend... ($i/30)"
    sleep 2
done

echo "==> Deploy complete"
docker-compose -f "$COMPOSE_FILE" ps