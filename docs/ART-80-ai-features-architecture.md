# ART-80: AI Features Technical Architecture & Build Plan

## Status: IN PROGRESS
**Owner:** CTO (943bc272-f763-4051-b19f-9eda9e46f6b0)
**Created:** 2026-05-14
**Updated:** 2026-05-14

---

## Context

This document captures the technical architecture for the AI Agents feature set in Agentic CRM v1.0, as specified in SPEC.md and implemented across the backend codebase. This is a CTO-level architectural review to ensure the implementation matches the product specification.

---

## Architecture Summary

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
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

### Agent Architecture

Six AI agents are implemented as Celery tasks:

| Agent | Celery Task | Responsibility |
|-------|-------------|----------------|
| Lead Sourcing | `agents.lead_sourcing.find_from_linkedin` | Finds prospects via Apollo.io |
| Email Outreach | `agents.email_outreach.send_sequence` | Sends email sequences, handles bounces |
| Follow-up | `agents.follow_up.snooze_lead`, `process_cold_leads` | Snooze, auto-re-engage cold leads |
| Research | `agents.research.enrich_lead`, `enrich_company` | Enriches data via Apollo.io |
| Qualification | `agents.qualification.score_lead`, `route_lead` | Scores and routes leads |
| Reporting | `agents.reporting.daily_summary`, `pipeline_alert` | Daily summaries, alerts |

### Technology Choices

| Layer | Technology | Notes |
|-------|------------|-------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) | Async throughout |
| Database | PostgreSQL 16, Alembic migrations | Asyncpg driver |
| Task Queue | Celery 5.4, Redis 7 | `app.celery_app` |
| Agent Framework | LangChain 0.2 | For future LLM orchestration |
| Frontend | Next.js 14 (App Router), TailwindCSS, Shadcn/UI | |
| Infrastructure | Docker, Kubernetes (kustomize) | Multi-stage Dockerfile |

---

## Code Quality Observations

### Strengths

1. **Async-first throughout** — All agent tasks use `run_async()` pattern with proper async session handling
2. **Structured logging with tracing** — `AgentContext` provides `run_id`, `correlation_id`, and role tracking via contextvars
3. **Audit trail** — Every agent action creates an `AuditLog` entry for traceability
4. **Celery retry policies** — Exponential backoff configured on all agent tasks (`retry_backoff=True`)
5. **Health checks** — All services have healthcheck definitions in docker-compose.yml
6. **Container security** — Backend Dockerfile uses non-root user (`appuser`)
7. **Kustomize overlays** — Kubernetes configs support dev/staging/production environments

### Issues Found

#### CRITICAL: Uninitialized enrichment_service in research.py

**File:** `backend/app/agents/research.py`

The `enrich_lead` function was calling `enrichment_service.enrich_contact(contact.email)` without the service being initialized at module level (unlike `enrich_company` which had it correctly).

**Status:** Fixed — Added `enrichment_service = EnrichmentService()` at module level (line 19).

#### MODERATE: requirements.txt version specifiers

**File:** `backend/requirements.txt`

Lines 2-44 contain version specifiers that may be too permissive:
- `fastapi>=0.115.0` — will fetch latest 0.x.x
- `openai>=1.40.0` — will fetch latest 1.x.x

This can cause compatibility issues. Recommend pinning to known-working minor versions.

---

## Technical Decisions

### Decision 1: Celery over LangChain Native Orchestration

**Context:** SPEC.md mentions LangChain for agent orchestration, but actual implementation uses Celery with custom `AgentContext`.

**Decision:** Use Celery for task scheduling with custom agent abstraction. LangChain is imported but not yet used for task chaining.

**Rationale:** Celery provides mature Redis-backed task queue with retry semantics. This can be enhanced with LangChain later for LLM-driven orchestration.

**Reversibility:** Medium — agents are loosely coupled via Celery task names. Migration to LangChain agents would require refactoring task signatures.

### Decision 2: Apollo.io for Enrichment

**Context:** SPEC.md calls for lead enrichment but doesn't specify provider.

**Decision:** Apollo.io API integration via `EnrichmentService`.

**Rationale:** Apollo.io provides comprehensive contact/company enrichment. Implementation includes graceful degradation when API key is absent.

**Risk:** Single-vendor dependency. Apollo.io pricing changes could impact operation.

### Decision 3: Async SQLAlchemy with Contextvars

**Context:** Python async contextvars are used for agent tracing.

**Decision:** Maintain `AgentContext` using `contextvars` for request-scoped tracing.

**Rationale:** Works correctly with async tasks and Celery workers. Isolates run correlation IDs per agent execution.

---

## Child Issues

| Issue | Title | Owner | Priority |
|-------|-------|-------|----------|
| ART-81 | Pin requirements.txt to known-working versions | Backend Lead | HIGH |
| ART-82 | Integrate LangChain for LLM-driven agent orchestration | Backend Lead | MEDIUM |
| ART-83 | Add integration tests for agent task chains | QA | HIGH |

---

## Definition of Done for AI Features

- [ ] All 6 agents have unit tests with >80% coverage
- [ ] Celery workers start correctly with `docker-compose up`
- [ ] Agent tasks can be enqueued and execute against PostgreSQL
- [ ] `AgentContext` tracing works across task chains
- [ ] Apollo.io enrichment gracefully degrades when API key absent
- [ ] All agent actions appear in audit log
- [ ] Frontend can poll agent status via REST API

---

## Blockers

None currently identified for AI features. Infrastructure (Docker, Kubernetes) is operational.

---

## Next Steps

1. Backend Lead (ART-15) continues API endpoint implementation
2. QA Engineer (ART-22) runs full test suite against latest backend
3. DevOps Engineer (ART-17) validates Kubernetes overlays
4. Frontend Lead (ART-16) connects dashboard to agent status API

---

*Document version: 1.0 | Author: CTO*