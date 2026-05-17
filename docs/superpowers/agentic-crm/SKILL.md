---
name: agentic-crm
description: Agentic CRM browser automation and API integration for OpenClaw. AI-first CRM where agents do the work, humans supervise. Automate lead capture from web forms, outreach logging, and dashboard monitoring. Use the Python SDK or MCP server for CRM API access.
---

# Agentic CRM — OpenClaw Skill

OpenClaw skill for browser automation and API integration with Agentic CRM. Automates lead capture, outreach logging, and pipeline monitoring workflows.

## CRM Access

### Python SDK (Recommended)

```python
from agentic_crm_sdk import AgenticCRM

crm = AgenticCRM(config={
    "base_url": "http://localhost:8000",
    "api_key": "your-api-key",  # from /api/auth/login
    "timeout": 30,
    "max_retries": 3
})

# Leads
crm.leads.list(filters={"stage": "new", "limit": 10})
crm.leads.create(data={"contact_id": 1, "source": "web", "score": 30})
crm.leads.update(id=1, data={"stage": "contacted", "score": 50})

# Contacts
crm.contacts.create(data={"email": "john@acme.com", "first_name": "John", "last_name": "Doe"})

# Deals
crm.deals.create(data={"contact_id": 1, "value": 15000, "stage": "lead"})
crm.deals.update(id=1, data={"stage": "qualified"})

# Activities
crm.activities.create(data={"lead_id": 1, "type": "note_added", "content": "Follow-up call scheduled"})

# Sequences
crm.sequences.list()
crm.sequences.enroll(lead_id=1, sequence_id=1)
```

### MCP Server

The MCP server runs at `/api/mcp` and exposes tools for CRM operations:

```
POST /api/mcp  — MCP protocol endpoint
```

## Browser Automation Workflows

### 1. Lead Capture from Web Forms

Monitor web forms and push new leads to CRM in real-time.

```python
# When a form submission is detected on your website:
lead_data = {
    "name": "Jane Smith",
    "email": "jane@startup.io",
    "phone": "+1-555-0123",
    "company": "Startup.io",
    "message": "Interested in enterprise plan",
    "source_url": "https://yoursite.com/contact",
    "utm_source": "google",
    "utm_campaign": "q1-prospecting"
}

# Push to CRM via webhook (fastest) or SDK
import requests

response = requests.post(
    "http://localhost:8000/api/webhooks/inbound/form",
    json={
        "name": lead_data["name"],
        "email": lead_data["email"],
        "phone": lead_data.get("phone"),
        "company": lead_data.get("company"),
        "message": lead_data.get("message"),
        "source_url": lead_data["source_url"],
        "utm_source": lead_data.get("utm_source"),
        "utm_campaign": lead_data.get("utm_campaign"),
    },
    headers={"X-Webhook-Secret": "your-webhook-secret"}
)
# Returns: {"status": "created", "lead_id": 123}
```

For bulk imports, use the SDK:
```python
for form_submission in pending_leads:
    crm.leads.create(data={
        "contact_id": crm.contacts.create(data={"email": form_submission["email"], ...}).id,
        "source": "web",
        "score": 25  # Base score for web leads
    })
```

### 2. Outreach Result Logging

Log email/LinkedIn outreach actions back to CRM for activity tracking.

```python
# Log an email sent event
crm.activities.create(data={
    "lead_id": 123,
    "contact_id": 45,
    "type": "email_sent",
    "content": "Sent intro email about enterprise plan",
    "activity_meta": {
        "message_id": "msg_abc123",  # For tracking opens/replies
        "sequence_id": 5,
        "step": 1
    }
})

# Log email opened (via webhook or polling)
crm.activities.create(data={
    "lead_id": 123,
    "contact_id": 45,
    "type": "email_opened",
    "content": "Lead opened intro email",
    "activity_meta": {"message_id": "msg_abc123", "opened_at": "2026-05-17T10:30:00Z"}
})

# Log email replied
crm.activities.create(data={
    "lead_id": 123,
    "contact_id": 45,
    "type": "email_replied",
    "content": "Lead replied: 'Yes, let's schedule a call'",
    "activity_meta": {"message_id": "msg_abc123", "reply_body": "Yes, let's..."}
})

# Log LinkedIn connection
crm.activities.create(data={
    "lead_id": 123,
    "contact_id": 45,
    "type": "linkedin_connection",
    "content": "Connected on LinkedIn",
    "activity_meta": {"linkedin_url": "https://linkedin.com/in/janedoe"}
})

# Log call made
crm.activities.create(data={
    "lead_id": 123,
    "contact_id": 45,
    "type": "call_made",
    "content": "Discovery call - 25 minutes",
    "activity_meta": {"duration_seconds": 1500, "outcome": "interested"}
})
```

### 3. Dashboard Monitoring — Stalled Deal Alerts

Periodic check for stalled deals and trigger alerts.

```python
from datetime import datetime, timedelta

# Find leads with no activity in 7+ days
seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

# Via SDK - list all leads and filter
all_leads = crm.leads.list(filters={"stage__in": ["contacted", "qualified", "proposal"]})

stalled = []
for lead in all_leads:
    activities = crm.activities.list(filters={"lead_id": lead["id"]})
    last_activity = activities[0] if activities else None
    if last_activity:
        last_date = last_activity.get("created_at", "")
        if last_date and last_date < seven_days_ago:
            stalled.append({
                "lead_id": lead["id"],
                "contact": lead.get("contact", {}).get("email"),
                "stage": lead["stage"],
                "score": lead["score"],
                "days_inactive": (datetime.utcnow() - datetime.fromisoformat(last_date)).days
            })

# Alert on stalled deals
for s in stalled:
    print(f"ALERT: Lead {s['contact']} ({s['lead_id']}) "
          f"in stage '{s['stage']}' has been inactive for {s['days_inactive']} days")
```

For Celery-based periodic monitoring, use the reporting agent tasks:
```python
from app.agents.reporting import stalled_lead_warning
stalled_lead_warning.delay(threshold_days=7)
```

## Key Entities

| Entity | Fields | Notes |
|--------|--------|-------|
| contacts | id, email, first_name, last_name, phone, company_id | Unique by email |
| companies | id, name, domain, industry, size, linkedin_url | Company info |
| leads | id, contact_id, score (0-100), stage, source, assigned_agent_id | Lead pipeline |
| deals | id, contact_id, value, stage, expected_close_date | Deal tracking |
| activities | id, lead_id, contact_id, type, content, activity_meta | Activity timeline |

### Lead Stages

`new` → `contacted` → `qualified` → `proposal` → `negotiation` → `won` / `lost`

### Activity Types

`email_sent`, `email_opened`, `email_replied`, `linkedin_message`, `linkedin_connection`, `call_made`, `call_received`, `note_added`, `meeting_scheduled`, `stage_changed`, `agent_action`

## Webhooks

Receive real-time events from external systems:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/webhooks/inbound/email` | Inbound email leads |
| `POST /api/webhooks/inbound/form` | Web form submissions |
| `POST /api/webhooks/email/bounce` | Bounce notifications |
| `POST /api/webhooks/email/open` | Email open tracking |
| `POST /api/webhooks/email/reply` | Email reply tracking |

All webhook endpoints require `X-Webhook-Secret` header validation.

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentic_crm
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<generate-with-python -c "import secrets; print(secrets.token_hex(32))">
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
APOLLO_API_KEY=<from apollo.io settings>
TWILIO_ACCOUNT_SID=<from twilio console>
TWILIO_AUTH_TOKEN=<from twilio console>
WEBHOOK_SECRET=<your-webhook-secret>
```

## Tech Stack

- Python 3.12+ / FastAPI / SQLAlchemy async / PostgreSQL 16
- Celery + Redis for background agents
- Alembic for migrations
- LangChain for agent orchestration