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
    data_dict = data.model_dump()
    # Convert list fields to JSON strings for SQLite storage
    _convert_lists_to_json(data_dict, ["tags"])
    lead = await prisma.lead.create(data=data_dict)
    # Re-fetch with contact relation
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

    update_data = data.model_dump(exclude_unset=True)
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
    """Convert Prisma model to dict, parsing JSON string fields."""
    d = {}
    for key, value in obj.model_dump().items():
        if key in ("tags", "extra_data") and isinstance(value, str):
            try:
                d[key] = json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                d[key] = value if value else []
        else:
            d[key] = value
    return d


def _convert_lists_to_json(data: dict, fields: list):
    """Convert list fields to JSON string for Prisma/SQLite storage."""
    for field in fields:
        if field in data and data[field] is not None:
            data[field] = json.dumps(data[field])