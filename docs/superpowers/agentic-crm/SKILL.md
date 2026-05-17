---
name: agentic-crm
description: Agentic CRM backend - FastAPI Python 3.12, PostgreSQL 16, Celery, Redis. Agents do the work, humans supervise. Supports lead management, pipeline, email/LinedIn outreach, Apollo.io enrichment, Twilio phone, webhooks, AI agents (lead_sourcing, email_outreach, follow_up, research, qualification, reporting).
---

# Agentic CRM Backend

Open-source AI-first CRM where agents are first-class actors.

## Tech Stack

- Python 3.12+ / FastAPI / SQLAlchemy async / PostgreSQL 16
- Celery + Redis for task queue
- LangChain for agent orchestration
- Alembic for migrations

## Project Structure

```
/root/agentic-crm/backend/
├── app/
│   ├── agents/          # Celery tasks (lead_sourcing, email_outreach, follow_up, research, qualification, reporting)
│   ├── api/             # FastAPI routers (leads, deals, contacts, companies, activities, agents, sequences, webhooks, dashboard)
│   ├── core/             # Config, security, rate limiting
│   ├── db/               # Database connection, Base
│   ├── models/           # SQLAlchemy models (User, Contact, Company, Lead, Deal, Activity, Sequence, AuditLog)
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic (email, enrichment, linkedin, phone, ga4, hubspot)
│   └── main.py           # FastAPI app entry point
├── alembic/              # Database migrations
├── tests/                # pytest fixtures and tests
├── agentic_crm_sdk/      # Python SDK for external integration
└── requirements.txt
```

## Key Entities

- `contacts` — name, email, phone, company relationship
- `companies` — name, domain, industry, size, linkedin_url
- `leads` — contact_id, score (0-100), stage (new/contacted/qualified/proposal/negotiation/won/lost), source, assigned_agent
- `deals` — contact_id, value, stage, expected_close_date
- `activities` — lead_id, type (email_sent/opened/replied, linkedin_message/connection, call_made/received, note_added, meeting_scheduled, stage_changed, agent_action)
- `agents` — name, role (lead_sourcing/research/outreach/follow_up/qualification/reporting), status (active/paused/stopped), config JSON
- `sequences` — name, steps with cadence (email/linkedin/phone)
- `audit_log` — append-only record of all agent actions

## Agent Roles

| Role | File | Responsibility |
|------|------|----------------|
| lead_sourcing | agents/lead_sourcing.py | Find prospects on LinkedIn via Apollo.io |
| email_outreach | agents/email_outreach.py | Send email sequences, handle bounces |
| follow_up | agents/follow_up.py | Snooze management, auto-re-engage cold leads |
| research | agents/research.py | Enrich lead/company data from Apollo.io |
| qualification | agents/qualification.py | Score and route leads |
| reporting | agents/reporting.py | Daily summaries, pipeline alerts |

## API Endpoints

- `POST /api/auth/*` — Authentication (login, refresh)
- `GET/POST /api/leads` — Lead CRUD
- `GET/POST /api/deals` — Deal CRUD
- `GET/POST /api/contacts` — Contact CRUD
- `GET/POST /api/companies` — Company CRUD
- `GET/POST /api/activities` — Activity logging
- `GET/POST /api/agents` — Agent management
- `GET/POST /api/sequences` — Email/LinkedIn sequences
- `GET /api/dashboard/*` — Dashboard metrics
- `POST /api/webhooks/inbound/*` — Inbound lead ingestion (email, form)
- `POST /api/webhooks/email/bounce` — Bounce handling
- `POST /api/webhooks/email/open` — Email open tracking
- `POST /api/webhooks/email/reply` — Email reply tracking

## Running the Backend

```bash
cd /root/agentic-crm/backend
source venv/bin/activate

# Development
fastapi dev app/main.py

# Run Celery worker
celery -A app.celery_app worker --loglevel=info

# Run migrations
alembic upgrade head

# Run tests
pytest
```

## Environment Variables

See `/root/agentic-crm/backend/.env.example`:
- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Celery broker
- `SECRET_KEY` — JWT tokens
- `SMTP_*` — Email sending
- `APOLLO_API_KEY` — Lead enrichment
- `TWILIO_*` — Phone integration
- `HUBSPOT_*` — CRM sync

## Database

PostgreSQL 16 with async SQLAlchemy. Models defined in `app/models/models.py`. Use Alembic migrations in `alembic/versions/` for schema changes.

## Agent Context

Agents use `AgentContext(role=AgentRole.XXX)` for logging context and support `correlation_id` for distributed tracing across task chains. All Celery tasks are defined with proper retry policies (`max_retries=3`, `retry_backoff=True`).

## Services Layer

- `email_service.py` — SMTP sending, templates, tracking
- `enrichment_service.py` — Apollo.io integration, contact search
- `linkedin_service.py` — Connection requests, messaging
- `phone_service.py` — Twilio call logging
- `ga4_service.py` — Google Analytics 4 server-side tracking
- `hubspot_service.py` — HubSpot CRM sync

## SDK

`agentic_crm_sdk/` is a Python SDK for external integration with the CRM API. Use `AgenticCRM(config=dict(base_url="...", api_key="..."))` to instantiate.

## Testing

pytest with fixtures in `tests/conftest.py`. Key fixtures: `db_session`, `test_user`, `test_contact`, `test_company`, `test_lead`, `test_deal`, `test_sequence`.