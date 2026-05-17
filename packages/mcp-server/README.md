# Agentic CRM MCP Server

Model Context Protocol server for Agentic CRM AI agents.

## Installation

```bash
pip install .
```

## Configuration

Environment variables:
- `AGENTIC_CRM_API_URL` - Base URL for the Agentic CRM API (default: http://localhost:8000)
- `AGENTIC_CRM_API_KEY` - API key for authentication (optional)

## Usage

```bash
mcp-server
```

## Tools

- `leads_list` - List leads with optional filtering
- `lead_get` - Get a lead by ID
- `lead_create` - Create a new lead
- `lead_update` - Update a lead
- `lead_delete` - Delete a lead
- `contact_create` - Create a contact
- `company_create` - Create a company
- `deal_create` - Create a deal
- `agent_list` - List agents
- `agent_pause` - Pause an agent
- `agent_resume` - Resume an agent
- `sequence_trigger` - Trigger a sequence for a lead
- `webhook_register` - Register a webhook