# SQLite Migration — Design

**Date:** 2026-05-17
**Project:** agentic-crm → SQLite-only
**Status:** Approved

---

## 1. Overview

Replace the full PostgreSQL + Redis + Celery stack with SQLite as the sole database and FastAPI `BackgroundTasks` for async agent jobs. Remove all container orchestration for postgres, redis, and celery. Single-container deployment.

**Constraints:**
- No existing data to preserve
- Replace entirely (not add SQLite as an option alongside PG)
- Agents run via FastAPI BackgroundTasks (Option B — confirmed by user)

---

## 2. Stack Changes

| Component | Before | After |
|-----------|--------|-------|
| Database | PostgreSQL 16 + asyncpg | SQLite + aiosqlite |
| Migrations | Alembic (PostgreSQL) | Alembic (SQLite dialect) |
| Task queue | Celery + Redis broker | FastAPI `BackgroundTasks` |
| Redis | Broker + cache | **Removed** |
| Docker Compose | 4 services (postgres, redis, backend, frontend) | 2 services (backend, frontend) |
| Kubernetes infra | postgres, redis, celery manifests | Removed |
| Health endpoints | `/health/db`, `/health/redis`, `/health/elasticsearch` | `/health/db` only |

---

## 3. Files to Change

### Backend — Core

| File | Change |
|------|--------|
| `app/db/database.py` | Swap `asyncpg` → `aiosqlite`. Remove connection pool. SQLite URL via env. |
| `app/core/config.py` | Add `DATABASE_URL` default for SQLite. Remove Redis/Celery URL fields (keep `redis_url` placeholder for compatibility). Simplify health checks. |
| `app/core/clients.py` | Remove `RedisClient`, `ElasticsearchClient`, all Redis/ES health checks, `check_all_health()`, `check_redis_health()`. Keep `check_database_health()`. |
| `app/celery_app.py` | **Delete** — no more Celery. |
| `app/agents/_async.py` | Delete `run_async` and `async_task`. |
| `app/main.py` | Remove Celery imports. Remove `/health/redis`, `/health/elasticsearch`, `/health/detailed` endpoints. Simplify lifespan. |

### Backend — Agent Modules

Each agent file (`email_outreach.py`, `follow_up.py`, `lead_sourcing.py`, `research.py`, `qualification.py`, `reporting.py`) gets the same transformation:

**Before:**
```python
from app.celery_app import celery_app
from app.agents._async import run_async

@celery_app.task(bind=True, max_retries=3, ...)
def send_sequence(self, lead_id, ...):
    ...
    return run_async(_send_sequence())
```

**After:**
```python
from fastapi import BackgroundTasks

def send_sequence_task(lead_id, ...):
    """Standalone async function — called by BackgroundTasks."""
    ...

async def send_sequence(lead_id, ...):
    """Async implementation."""
    ...
    return {"status": "sent", ...}
```

API route handlers call `BackgroundTasks.add_task(send_sequence, lead_id, ...)`.

### Backend — Config & Env

| File | Change |
|------|--------|
| `backend/requirements.txt` | Remove `asyncpg`, `celery`, `redis`. Keep `aiosqlite`. |
| `backend/.env.example` | Update DATABASE_URL default: `sqlite+aiosqlite:///./agentic_crm.db` |
| `backend/alembic.ini` | Change `sqlalchemy.url` to SQLite |
| `alembic/env.py` | May need dialect tweak if it auto-detects |

### Docker & Infra

| File | Change |
|------|--------|
| `docker-compose.yml` | Remove `postgres`, `redis`, `celeryworker`, `celerybeat` services. Keep `backend` and `frontend`. Backend env loses `REDIS_URL`, `CELERY_*` vars. |
| `backend/Dockerfile` | Remove any Celery/Redis install steps. |
| `infra/postgres.yaml` | **Delete** |
| `infra/redis.yaml` | **Delete** |
| `infra/celery.yaml` | **Delete** |
| `infra/kustomization.yaml` | Remove postgres/redis/celery references |

### Tests

| File | Change |
|------|--------|
| `backend/tests/conftest.py` | Already uses `sqlite+aiosqlite:///:memory:` — no change needed. |

---

## 4. Database URL Format

```bash
# Development
DATABASE_URL=sqlite+aiosqlite:///./agentic_crm.db

# Docker (file-backed)
DATABASE_URL=sqlite+aiosqlite:////app/data/agentic_crm.db

# Tests (already in-memory)
DATABASE_URL=sqlite+aiosqlite:///:memory:
```

---

## 5. Alembic Migration Strategy

Since the schema already exists as SQLAlchemy models and Alembic migrations, we switch the dialect to SQLite:

1. Update `alembic.ini` → `sqlite+aiosqlite://...`
2. Run existing migrations (Alembic will apply them to SQLite)
3. Some PostgreSQL-specific constructs may need tweaking:
   - `postgresql.JSON` → SQLite JSON column type (SQLAlchemy handles this)
   - `server_default` clauses may differ
   - Enum types — SQLite doesn't have native enums; use string columns

If migration errors occur, fix per-case. Since there's no data to preserve, destructive re-migration (drop all, regenerate) is acceptable.

---

## 6. Agent Execution Pattern

**API route → BackgroundTasks → async function**

Example (email_outreach):

```python
from fastapi import APIRouter, BackgroundTasks
from app.agents.email_outreach import send_sequence_task

@router.post("/sequences/{sequence_id}/send/{lead_id}")
async def send_sequence(
    sequence_id: int,
    lead_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_sequence_task, lead_id, sequence_id)
    return {"message": "Sequence task queued"}
```

Each `send_sequence_task` is a plain async function that was previously wrapped in `@celery_app.task`. No decorator, no `run_async` call needed. The function itself is `async def` — FastAPI's `BackgroundTasks` handles the event loop internally.

---

## 7. Removed Features (Known Scope)

- **Celery periodic tasks (celerybeat)** — scheduler-based recurring agent jobs. Replaced by:
  - FastAPI startup events for one-shot init tasks
  - External cron triggering API endpoints if recurring scheduling is needed
- **Redis caching** — any `RedisClient` usage for caching is removed. Simple in-process dict/lru_cache replaces it if needed.
- **Elasticsearch** — `es_client` and all ES health checks removed. Full-text search falls back to SQLite LIKE queries (or is dropped for MVP).
- **Celery retry logic** — `max_retries`, `retry_backoff`, `autoretry_for` are Celery-specific. Tasks no longer auto-retry; failures are logged and that's it.
- **Multi-instance horizontal scaling** — SQLite write lock means one instance only. This is acceptable given the self-hosted, single-instance target.

---

## 8. Health Check After Migration

```python
@app.get("/health/db")
async def health_db():
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "sqlite"}
    except Exception as e:
        return {"status": "unhealthy", "service": "sqlite", "error": str(e)}
```

No more `/health/redis`, `/health/elasticsearch`, `/health/detailed`.

---

## 9. Docker Compose (After)

```yaml
services:
  backend:
    # sqlite url, no postgres/redis/celery env vars
    environment:
      DATABASE_URL: sqlite+aiosqlite:////app/data/agentic_crm.db
    volumes:
      - ./data:/app/data   # persistent SQLite file
    # no depends_on postgres/redis

  frontend:
    # unchanged
```

---

## 10. Approvals

- [x] User confirmed: Replace entirely, no data to preserve, Option B (BackgroundTasks), reduce infrastructure
- [x] Design approved: this document

---

*Author: backend-lead | superpowers workflow Phase 1*