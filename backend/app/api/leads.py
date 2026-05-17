"""
Leads API routes
"""
import json
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.prisma import prisma
from app.schemas.schemas import LeadCreate, LeadResponse, LeadUpdate

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=list[LeadResponse])
@limiter.limit(settings.rate_limit_default)
async def list_leads(request: Request):
    leads = await prisma.lead.find_many(
        order={"id": "desc"},
        include={"contact": True},
    )
    # Prisma JSON fields are stored as JSON strings in SQLite
    results = []
    for lead in leads:
        lead_dict = _prisma_to_dict(lead)
        results.append(lead_dict)
    return results


@router.get("/{lead_id}", response_model=LeadResponse)
@limiter.limit(settings.rate_limit_default)
async def get_lead(lead_id: int, request: Request):
    lead = await prisma.lead.find_unique(
        where={"id": lead_id},
        include={"contact": True},
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _prisma_to_dict(lead)


@router.post("/", response_model=LeadResponse, status_code=201)
@limiter.limit(settings.rate_limit_default)
async def create_lead(data: LeadCreate, request: Request):
    data_dict = data.model_dump(by_alias=True)
    data_dict["contactId"] = data_dict.pop("contact_id")
    if "assigned_agent_id" in data_dict:
        data_dict["assignedAgentId"] = data_dict.pop("assigned_agent_id")
    _convert_lists_to_json(data_dict, ["tags"])
    lead = await prisma.lead.create(data=data_dict)
    lead = await prisma.lead.find_unique(
        where={"id": lead.id},
        include={"contact": True},
    )
    return _prisma_to_dict(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
@limiter.limit(settings.rate_limit_default)
async def update_lead(lead_id: int, data: LeadUpdate, request: Request):
    existing = await prisma.lead.find_unique(where={"id": lead_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = data.model_dump(exclude_unset=True, by_alias=True)
    rename_fields = {
        "contact_id": "contactId",
        "assigned_agent_id": "assignedAgentId",
        "snooze_until": "snoozeUntil",
        "last_contacted_at": "lastContactedAt",
        "utm_source": "utmSource",
        "utm_medium": "utmMedium",
        "utm_campaign": "utmCampaign",
        "utm_term": "utmTerm",
        "utm_content": "utmContent",
        "hubspot_contact_id": "hubspotContactId",
        "ga_client_id": "gaClientId",
    }
    for old_key, new_key in rename_fields.items():
        if old_key in update_data:
            update_data[new_key] = update_data.pop(old_key)

    if "tags" in update_data:
        _convert_lists_to_json(update_data, ["tags"])

    lead = await prisma.lead.update(
        where={"id": lead_id},
        data=update_data,
    )
    lead = await prisma.lead.find_unique(
        where={"id": lead_id},
        include={"contact": True},
    )
    return _prisma_to_dict(lead)


@router.delete("/{lead_id}")
@limiter.limit(settings.rate_limit_default)
async def delete_lead(lead_id: int, request: Request):
    existing = await prisma.lead.find_unique(where={"id": lead_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")
    await prisma.lead.delete(where={"id": lead_id})
    return {"deleted": True}


@router.post("/{lead_id}/score")
@limiter.limit(settings.rate_limit_default)
async def rescore_lead(lead_id: int, request: Request, background_tasks: BackgroundTasks):
    """Recalculate lead score using the qualification agent"""
    from app.agents.qualification import score_lead
    background_tasks.add_task(score_lead, lead_id)
    return {"message": "Lead scoring task queued", "lead_id": lead_id}


@router.post("/{lead_id}/route")
@limiter.limit(settings.rate_limit_default)
async def route_lead(lead_id: int, request: Request, background_tasks: BackgroundTasks):
    """Route lead to appropriate agent using the qualification agent"""
    from app.agents.qualification import route_lead
    background_tasks.add_task(route_lead, lead_id)
    return {"message": "Lead routing task queued", "lead_id": lead_id}


@router.post("/{lead_id}/enrich")
@limiter.limit(settings.rate_limit_default)
async def enrich_lead(lead_id: int, request: Request, background_tasks: BackgroundTasks):
    """Enrich lead data from Apollo.io using the research agent"""
    from app.agents.research import enrich_lead
    background_tasks.add_task(enrich_lead, lead_id)
    return {"message": "Lead enrichment task queued", "lead_id": lead_id}


def _prisma_to_dict(obj) -> dict:
    """Convert Prisma model to dict, parsing JSON string fields and converting camelCase to snake_case recursively."""
    d = {}
    json_fields = ("tags", "extra_data")
    for key, value in obj.model_dump().items():
        snake_key = _camel_to_snake(key)
        if key in json_fields and isinstance(value, str):
            try:
                parsed = json.loads(value) if value else None
                if key == "extra_data":
                    d[snake_key] = parsed if parsed is not None else {}
                else:
                    d[snake_key] = parsed if parsed is not None else []
            except (json.JSONDecodeError, TypeError):
                if key == "extra_data":
                    d[snake_key] = {}
                else:
                    d[snake_key] = value
        elif key in json_fields and value is None:
            d[snake_key] = {} if key == "extra_data" else []
        elif isinstance(value, dict):
            d[snake_key] = _convert_dict_keys(value)
        elif hasattr(value, 'model_dump'):
            d[snake_key] = _prisma_to_dict(value)
        else:
            d[snake_key] = value
    return d


def _convert_dict_keys(d: dict) -> dict:
    """Convert all keys in a dict from camelCase to snake_case recursively."""
    result = {}
    for key, value in d.items():
        snake_key = _camel_to_snake(key)
        if isinstance(value, dict):
            result[snake_key] = _convert_dict_keys(value)
        elif isinstance(value, list):
            result[snake_key] = [
                _convert_dict_keys(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[snake_key] = value
    return result


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _convert_lists_to_json(data: dict, fields: list):
    """Convert list fields to JSON string for Prisma/SQLite storage."""
    for field in fields:
        if field in data and data[field] is not None:
            data[field] = json.dumps(data[field])