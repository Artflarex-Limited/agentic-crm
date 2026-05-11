# Agentic CRM Infrastructure

Production-ready Docker, Kubernetes, and CI/CD infrastructure for Agentic CRM.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                         │
├──────────────┬───────────────┬──────────────────────────────┤
│  Next.js     │   FastAPI     │   Celery Workers             │
│  Frontend    │   Backend     │   (Agent Jobs)                │
│  :3000       │   :8000       │                              │
├──────────────┼───────────────┼──────────────────────────────┤
│              │               │   Redis (Queue/Cache)       │
│              │   PostgreSQL  │                              │
│              │   (Leads/     │                              │
│              │   Deals)      │                              │
└──────────────┴───────────────┴──────────────────────────────┘
```

## Quick Start

```bash
# Copy environment variables
cp .env.example .env

# Start all services
make up

# View logs
make logs

# Stop services
make down
```

## Development Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make build` | Build Docker images |
| `make test` | Run pytest |
| `make lint` | Run ruff and black |
| `make migrate` | Run Alembic migrations |
| `make seed` | Seed database with sample data |
| `make backup` | Create PostgreSQL backup |
| `make logs-backend` | View backend logs |
| `make logs-frontend` | View frontend logs |
| `make worker` | Start Celery worker |
| `make deploy` | Deploy to production |

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js 14 dashboard |
| backend | 8000 | FastAPI REST API |
| postgres | 5432 | PostgreSQL 16 database |
| redis | 6379 | Redis 7 message queue |
| celeryworker | - | Celery background workers |
| celerybeat | - | Celery scheduled tasks |
| nginx | 80 | Reverse proxy (production) |

## Kubernetes

Manifests are in `kubernetes/`:
- `postgres.yaml` - StatefulSet + Service for PostgreSQL
- `redis.yaml` - StatefulSet + Service for Redis
- `backend.yaml` - Deployment + Service for FastAPI
- `celery.yaml` - Deployments for Celery worker and beat
- `frontend.yaml` - Deployment + Service for Next.js
- `ingress.yaml` - NGINX Ingress with TLS
- `configmap.yaml` - Non-secret configuration
- `secret.yaml` - Template for secrets
- `pvc.yaml` - PersistentVolumeClaims
- `kustomization.yaml` - Kustomize overlay

## CI/CD

GitHub Actions workflows:
- `.github/workflows/ci.yml` - Lint, test, build, security scan
- `.github/workflows/cd.yml` - Deploy to Kubernetes on main

## Scripts

- `scripts/deploy.sh` - Production deployment with health checks
- `scripts/migrate.sh` - Run database migrations
- `scripts/seed.sh` - Seed database with sample data
- `scripts/backup.sh` - PostgreSQL backup to local

## Environment Variables

See `.env.example` for all required environment variables.

## License

MIT