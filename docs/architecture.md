# Architecture

## System Overview

Agentic CRM uses a microservices-inspired architecture with three primary components:

- **Frontend**: Next.js 14 SPA
- **Backend**: FastAPI REST API
- **Workers**: Celery-based async job processing

## Component Communication

- Frontend → Backend: HTTP REST
- Backend → Workers: Redis task queue (Celery)
- Workers → External APIs: Direct (LinkedIn, Twilio, email providers)
- All components share a PostgreSQL database

## Frontend (Next.js 14)

Location: `/frontend`

- Serves the React SPA
- Communicates with Backend via REST API
- Uses React Query for server state management
- Uses Zustand for client state management

## Backend (FastAPI + Python 3.12+)

Location: `/backend`

- Exposes REST API at port 8000
- Manages PostgreSQL database via SQLAlchemy ORM
- Queues async tasks to Celery via Redis
- Runs Alembic migrations for schema management

## Workers (Celery + Redis)

Location: `/backend/app/agents`

- **Lead Sourcing Agent**: Finds prospects via LinkedIn, web, forms
- **Research Agent**: Enriches lead data (company info, contacts, news)
- **Outreach Agent**: Sends emails/LinkedIn messages via sequences
- **Follow-up Agent**: Auto-re-engages cold leads, schedules follow-ups
- **Qualification Agent**: Scores and routes leads, updates stages
- **Reporting Agent**: Daily summaries, pipeline alerts, stalled deal warnings

## Database Schema

Core entities in PostgreSQL:

- `contacts` — name, email, phone, company, source
- `companies` — name, domain, industry, size
- `leads` — contact_id, score, stage, assigned_agent
- `deals` — contact_id, value, stage, expected_close_date
- `activities` — lead_id, agent_id, type, content, timestamp
- `agents` — name, role, status (active/paused), config
- `sequences` — name, steps (email/LinkedIn/phone), cadence
- `audit_log` — everything agents do (append-only)

## Deployment

### Development

Docker Compose orchestrates all services locally.

### Production

Kubernetes manifests in `/kubernetes`:

- StatefulSets for PostgreSQL and Redis
- Deployments for FastAPI, Next.js, Celery workers/beat
- NGINX Ingress for routing and TLS termination
- Kustomize overlays for environment-specific configuration
