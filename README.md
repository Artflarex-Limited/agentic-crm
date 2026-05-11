# Agentic CRM

> Open-source CRM built for AI agents. Humans supervise; agents do the work.

## Overview

Agentic CRM is a cloud-native, open-source Customer Relationship Management system where **AI agents are first-class actors**. Unlike traditional CRMs where humans do all the work and AI assists, Agentic CRM inverts this: agents find leads, qualify them, follow up, and manage the pipeline autonomously — with humans overseeing, approving, and stepping in only when needed.

## Features

- **Lead Management** — Create, enrich, score, and route leads automatically
- **Pipeline Management** — Visual Kanban-style pipeline with deal tracking
- **AI Agents** — Lead Sourcing, Research, Outreach, Follow-up, Qualification, and Reporting agents
- **Human Dashboard** — Pipeline view, activity feed, approval queue, and audit trail
- **Integrations** — Email (SMTP/Gmail/Outlook), LinkedIn, Phone (Twilio), Webhooks, REST API

## Architecture

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

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, PostgreSQL 16, SQLAlchemy, Celery + Redis
- **Frontend:** Next.js 14, TailwindCSS, Shadcn/UI, React Query, Zustand
- **Infrastructure:** Docker, Kubernetes, Nginx

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

## Project Structure

```
agentic-crm/
├── backend/            # FastAPI REST API
│   ├── app/
│   │   ├── agents/    # AI agent implementations
│   │   ├── models/    # SQLAlchemy models
│   │   ├── services/  # Business logic services
│   │   └── api/       # API routes
│   └── tests/         # Backend tests
├── frontend/           # Next.js 14 dashboard
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   └── lib/           # Utilities and API client
├── kubernetes/         # K8s manifests
├── docker-compose.yml # Docker Compose configuration
├── Makefile          # Development commands
└── SPEC.md           # Full product specification
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
