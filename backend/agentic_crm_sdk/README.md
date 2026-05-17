# Agentic CRM Python SDK

A Python SDK for interacting with the Agentic CRM API.

## Installation

```bash
pip install agentic-crm-sdk
```

Or from source:

```bash
cd agentic_crm_sdk
pip install -e .
```

## Quick Start

```python
from agentic_crm_sdk import AgenticCRM, SDKConfig

# Basic usage
client = AgenticCRM()

# With custom config
client = AgenticCRM(SDKConfig(
    base_url="https://api.example.com",
    api_key="your-api-key"
))

# List leads
response = client.leads.list()
print(response.json())

# Create a lead
lead = client.leads.create({
    "contact_id": 1,
    "source": "linkedin",
    "stage": "new"
})
```

## Async Client

For async applications, use `AsyncAgenticCRM`:

```python
import asyncio
from agentic_crm_sdk import AsyncAgenticCRM

async def main():
    client = AsyncAgenticCRM()

    # List leads
    response = await client.leads.list()
    print(response.json())

    # Create a lead
    lead = await client.leads.create({
        "contact_id": 1,
        "source": "linkedin",
        "stage": "new"
    })

asyncio.run(main())
```

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `base_url` | `http://localhost:8000` | Base URL for the API |
| `api_key` | `None` | API key for authentication |
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Maximum retry attempts |

## Available Clients

- `client.leads` - Lead management
- `client.contacts` - Contact management
- `client.deals` - Deal management
- `client.activities` - Activity tracking
- `client.agents` - Agent control
- `client.sequences` - Email sequences

## Examples

### Leads

```python
# List leads with filters
leads = client.leads.list(stage="qualified", limit=10)

# Get a single lead
lead = client.leads.get(123)

# Create lead
new_lead = client.leads.create({
    "contact_id": 1,
    "source": "email",
    "stage": "new",
    "score": 50
})

# Update lead
client.leads.update(123, {"stage": "contacted", "score": 75})

# Get lead activities
activities = client.leads.activities(123)

# Add note to lead
client.leads.add_note(123, "Follow up next week")
```

### Contacts

```python
# List contacts
contacts = client.contacts.list(company_id=5)

# Create contact
contact = client.contacts.create({
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "company_id": 5
})

# Update contact
client.contacts.update(contact_id, {"title": "VP Sales"})
```

### Deals

```python
# List deals
deals = client.deals.list(stage="proposal")

# Create deal
deal = client.deals.create({
    "contact_id": 1,
    "company_id": 5,
    "name": "Enterprise Deal",
    "value": 50000.0,
    "stage": "lead"
})

# Update deal stage
client.deals.update(deal_id, {"stage": "qualified"})
```

### Agents

```python
# List agents
agents = client.agents.list()

# Pause agent
client.agents.pause(agent_id)

# Resume agent
client.agents.resume(agent_id)
```

### Sequences

```python
# List sequences
sequences = client.sequences.list()

# Create sequence
sequence = client.sequences.create({
    "name": "Welcome Campaign",
    "steps": [
        {"type": "email", "delay_days": 0, "template": "welcome"},
        {"type": "email", "delay_days": 3, "template": "followup"}
    ]
})

# Enroll lead in sequence
client.sequences.enroll_lead(sequence_id=1, lead_id=123)
```

## Error Handling

```python
import httpx

try:
    response = client.leads.get(99999)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Lead not found")
    else:
        raise
```

## License

MIT License - Artflarex Solutions