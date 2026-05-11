# Agentic CRM — Product Specification

> Open-source CRM built for AI agents. Humans supervise; agents do the work.

---

## 1. Concept & Vision

Agentic CRM is a cloud-native, open-source Customer Relationship Management system where **AI agents are first-class actors**. Unlike traditional CRMs where humans do all the work and AI assists, Agentic CRM inverts this: agents find leads, qualify them, follow up, and manage the pipeline autonomously — with humans overseeing, approving, and stepping in only when needed.

**Core philosophy:** The system should feel like having an AI sales team that works 24/7, never forgets, and reports everything transparently.

---

## 2. Product Name

**Agentic CRM** (`agentic-crm`)

---

## 3. Open Core Model

- **Open Source (MIT License):** Full source code on GitHub. Free to self-host.
- **Paid Services (Artflarex sells):**
  - Managed cloud hosting (subscription)
  - Setup & onboarding
  - Custom agent development
  - Premium support

---

## 4. Target Users

| User | Use Case |
|------|----------|
| Small businesses | "I want a sales team but can't afford one" — AI handles everything |
| Sales agencies | Scale outreach without scaling headcount |
| SaaS founders | Automated lead management + qualification |
| Startups | Lean sales ops with AI agents |

---

## 5. Lead Channels (MVP)

- LinkedIn outreach
- Email (cold + inbound)
- Phone calls (integration)
- Website forms (inbound)
- Cold outreach campaigns

**Post-MVP:** Google Places API, Twitter/X, warm outreach

---

## 6. Core Features

### 6.1 Lead Management
- Create, enrich, score, and route leads automatically
- Lead source tracking (LinkedIn, email, web, phone)
- Custom fields and tags
- Duplicate detection
- Lead assignment (human or agent)

### 6.2 Pipeline Management
- Visual pipeline (Kanban-style or table)
- Deal stages: Lead → Qualified → Proposal → Negotiation → Won/Lost
- Deal value tracking
- Activity logging (calls, emails, notes)
- Deadline/snooze management

### 6.3 AI Agents (Core Differentiator)

| Agent | Responsibility |
|-------|---------------|
| **Lead Sourcing Agent** | Finds prospects on LinkedIn, web, forms |
| **Research Agent** | Enriches lead data (company info, contacts, news) |
| **Outreach Agent** | Sends emails/LinkedIn messages via sequences |
| **Follow-up Agent** | Auto-re-engages cold leads, schedules follow-ups |
| **Qualification Agent** | Scores and routes leads, updates stages |
| **Reporting Agent** | Daily summaries, pipeline alerts, stalled deal warnings |

### 6.4 Human Dashboard
- Pipeline view (all deals, all stages)
- Activity feed (what each agent is doing)
- Approval queue (human must approve outreach before send)
- Agent controls: pause, resume, override
- Full audit trail of all agent actions

### 6.5 Integrations
- Email (SMTP / Gmail / Outlook API)
- LinkedIn (via Apollo.io or similar)
- Twilio / Retell (phone calls)
- Webhook receiver (inbound leads)
- REST API (for custom integrations)

---

## 7. Tech Stack

### Backend
- **Language:** Python 3.12+ (agents, API)
- **Framework:** FastAPI (REST API)
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy + Alembic (migrations)
- **Task Queue:** Celery + Redis (agent job scheduling)
- **Agent Framework:** LangChain or custom orchestration

### Frontend
- **Framework:** Next.js 14 (App Router)
- **UI:** TailwindCSS + Shadcn/UI
- **State:** React Query (server state) + Zustand (client state)
- **Charts:** Recharts or Tremor

### Infrastructure
- **Container:** Docker + Docker Compose
- **Orchestration:** Kubernetes (production) / Docker Compose (development)
- **Reverse Proxy:** Nginx

---

## 8. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Docker Compose                       │
├────────────────┬────────────────┬─────────────────────────┤
│   nextjs-app   │   fastapi-api  │   celery-worker         │
│   (Frontend)   │   (REST API)   │   (Agent Jobs)          │
├────────────────┼────────────────┼─────────────────────────┤
│                │                │   redis (message queue) │
│                │   postgres     │                         │
│                │   (leads/deals)│   postgres (shared)     │
└────────────────┴────────────────┴─────────────────────────┘
```

---

## 9. Database Schema (Overview)

### Core Entities
- `contacts` — name, email, phone, company, source
- `companies` — name, domain, industry, size
- `leads` — contact_id, score, stage, assigned_agent
- `deals` — contact_id, value, stage, expected_close_date
- `activities` — lead_id, agent_id, type, content, timestamp
- `agents` — name, role, status (active/paused), config
- `sequences` — name, steps (email/LinkedIn/phone), cadence
- `audit_log` — everything agents do (append-only)

---

## 10. MVP Roadmap

### Month 1 — Foundation
- [ ] Docker Compose setup (postgres, redis, app)
- [ ] PostgreSQL schema (all core tables)
- [ ] FastAPI REST API (full CRUD for all entities)
- [ ] Next.js dashboard (pipeline view, lead list, agent status)
- [ ] Email ingestion (inbound leads via webhook)
- [ ] Basic lead scoring (rule-based)

### Month 2 — Agent Core
- [ ] Agent orchestration layer (Celery workers)
- [ ] Lead Sourcing Agent (LinkedIn scraping via Apollo.io)
- [ ] Email Outreach Agent (SMTP sequences)
- [ ] Research Agent (company/contact enrichment)
- [ ] Follow-up Agent (snooze, auto-re-engage)
- [ ] Human approval queue (outreach holds for human sign-off)

### Month 3 — Polish + Launch
- [ ] Phone integration (Twilio call logging)
- [ ] Reporting Agent (daily pipeline summaries)
- [ ] LinkedIn Agent (connection + message automation)
- [ ] Full audit trail UI
- [ ] GitHub release + documentation
- [ ] Landing page

---

## 11. Non-Goals (Out of Scope for MVP)

- Native mobile app
- Multi-tenant SaaS (self-hosted only for MVP)
- Advanced AI/ML scoring (vector embeddings post-MVP)
- White-label
- Payment integration (standalone for now)

---

## 12. Success Metrics

- 10+ leads tracked from first internal Artflarex use case
- At least 2 agents actively working in the system
- Outreach agent sending real emails within Month 2
- Clean dashboard with readable pipeline

---

*Document version: 1.0 | Last updated: 2026-05-11*