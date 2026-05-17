"""
MCP Tools for Agentic CRM

Exposes CRM operations as MCP tools that AI agents can call.
"""
from typing import Any

from fastmcp import FastMCP

from mcp_server import Settings, call_api

mcp = FastMCP("Agentic CRM")


@mcp.tool()
async def leads_list(stage: str | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """List leads with optional filtering by stage."""
    params = {"limit": limit, "offset": offset}
    if stage:
        params["stage"] = stage
    return await call_api("GET", "/api/leads", params=params)


@mcp.tool()
async def lead_get(lead_id: int) -> dict[str, Any]:
    """Get a lead by ID."""
    return await call_api("GET", f"/api/leads/{lead_id}")


@mcp.tool()
async def lead_create(
    contact_id: int,
    source: str = "other",
    stage: str = "new",
    score: int = 0,
    tags: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create a new lead."""
    data = {
        "contact_id": contact_id,
        "source": source,
        "stage": stage,
        "score": score,
        "tags": tags or [],
        "notes": notes,
    }
    return await call_api("POST", "/api/leads", json=data)


@mcp.tool()
async def lead_update(
    lead_id: int,
    stage: str | None = None,
    score: int | None = None,
    tags: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update a lead."""
    data = {}
    if stage is not None:
        data["stage"] = stage
    if score is not None:
        data["score"] = score
    if tags is not None:
        data["tags"] = tags
    if notes is not None:
        data["notes"] = notes
    return await call_api("PATCH", f"/api/leads/{lead_id}", json=data)


@mcp.tool()
async def lead_delete(lead_id: int) -> dict[str, Any]:
    """Delete a lead."""
    return await call_api("DELETE", f"/api/leads/{lead_id}")


@mcp.tool()
async def contact_create(
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    title: str | None = None,
    company_id: int | None = None,
) -> dict[str, Any]:
    """Create a new contact."""
    data = {"email": email}
    if first_name is not None:
        data["first_name"] = first_name
    if last_name is not None:
        data["last_name"] = last_name
    if phone is not None:
        data["phone"] = phone
    if title is not None:
        data["title"] = title
    if company_id is not None:
        data["company_id"] = company_id
    return await call_api("POST", "/api/contacts", json=data)


@mcp.tool()
async def company_create(
    name: str,
    domain: str | None = None,
    industry: str | None = None,
    size: str | None = None,
) -> dict[str, Any]:
    """Create a new company."""
    data = {"name": name}
    if domain is not None:
        data["domain"] = domain
    if industry is not None:
        data["industry"] = industry
    if size is not None:
        data["size"] = size
    return await call_api("POST", "/api/companies", json=data)


@mcp.tool()
async def deal_create(
    contact_id: int,
    name: str,
    value: float = 0.0,
    stage: str = "lead",
    expected_close_date: str | None = None,
) -> dict[str, Any]:
    """Create a new deal."""
    data = {"contact_id": contact_id, "name": name, "value": value, "stage": stage}
    if expected_close_date is not None:
        data["expected_close_date"] = expected_close_date
    return await call_api("POST", "/api/deals", json=data)


@mcp.tool()
async def agent_list() -> dict[str, Any]:
    """List all agents."""
    return await call_api("GET", "/api/agents")


@mcp.tool()
async def agent_pause(agent_id: int) -> dict[str, Any]:
    """Pause an agent."""
    return await call_api("POST", f"/api/agents/{agent_id}/pause")


@mcp.tool()
async def agent_resume(agent_id: int) -> dict[str, Any]:
    """Resume a paused agent."""
    return await call_api("POST", f"/api/agents/{agent_id}/resume")


@mcp.tool()
async def sequence_trigger(lead_id: int, sequence_id: int) -> dict[str, Any]:
    """Trigger a sequence for a lead."""
    return await call_api("POST", "/api/sequences/enroll", json={"lead_id": lead_id, "sequence_id": sequence_id})


@mcp.tool()
async def webhook_register(url: str, events: list[str]) -> dict[str, Any]:
    """Register a webhook endpoint."""
    return await call_api("POST", "/api/webhooks/register", json={"url": url, "events": events})


if __name__ == "__main__":
    mcp.run()