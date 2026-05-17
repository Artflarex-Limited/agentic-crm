"""
Deals API routes
"""
import json
from fastapi import APIRouter, HTTPException

from app.prisma import prisma
from app.schemas.schemas import DealCreate, DealResponse, DealUpdate
from app.services.rfq_service import get_rfq_service

router = APIRouter()


@router.get("/", response_model=list[DealResponse])
async def list_deals():
    deals = await prisma.deal.find_many(
        order={"id": "desc"},
        include={"contact": True, "company": True},
    )
    return [_prisma_to_dict(d) for d in deals]


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: int):
    deal = await prisma.deal.find_unique(
        where={"id": deal_id},
        include={"contact": True, "company": True},
    )
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _prisma_to_dict(deal)


@router.post("/", response_model=DealResponse, status_code=201)
async def create_deal(data: DealCreate):
    data_dict = data.model_dump(by_alias=True)
    data_dict["contactId"] = data_dict.pop("contact_id")
    if "company_id" in data_dict:
        data_dict["companyId"] = data_dict.pop("company_id")
    deal = await prisma.deal.create(data=data_dict)
    deal = await prisma.deal.find_unique(
        where={"id": deal.id},
        include={"contact": True, "company": True},
    )
    return _prisma_to_dict(deal)


@router.post("/from-lead/{lead_id}", response_model=DealResponse, status_code=201)
async def create_rfq_from_lead(
    lead_id: int,
    deal_name: str | None = None,
    deal_value: float = 0.0,
    expected_close_days: int = 30,
):
    """
    Generate an RFQ (deal) from a lead.
    Automates lead-to-deal conversion.
    """
    rfq_service = await get_rfq_service()
    result = await rfq_service.create_rfq_from_lead(
        lead_id=lead_id,
        deal_name=deal_name,
        deal_value=deal_value,
        expected_close_days=expected_close_days,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")

    deal = await prisma.deal.find_unique(
        where={"id": result["deal_id"]},
        include={"contact": True, "company": True},
    )
    if not deal:
        raise HTTPException(status_code=500, detail="RFQ creation failed")

    if deal.value and deal.value > 0:
        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        contact = deal.contact
        await ga4_service.track_generate_rfq(
            client_id=generate_ga_client_id(),
            deal_id=deal.id,
            deal_value=deal.value,
            lead_id=lead_id,
            user_email=contact.email if contact else None,
        )

    return _prisma_to_dict(deal)


@router.put("/{deal_id}/advance", response_model=DealResponse)
async def advance_rfq_stage(deal_id: int, target_stage: str):
    """
    Advance RFQ to next pipeline stage.
    """
    rfq_service = await get_rfq_service()
    success = await rfq_service.advance_rfq_stage(deal_id, target_stage)

    if not success:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal = await prisma.deal.find_unique(
        where={"id": deal_id},
        include={"contact": True, "company": True},
    )

    if deal and deal.value and deal.value > 0:
        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        contact = deal.contact
        await ga4_service.track_deal_stage_changed(
            client_id=generate_ga_client_id(),
            deal_id=deal.id,
            old_stage=str(deal.stage) if hasattr(deal.stage, "value") else str(deal.stage),
            new_stage=target_stage,
            deal_value=deal.value,
            user_email=contact.email if contact else None,
        )

    return _prisma_to_dict(deal)


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(deal_id: int, data: DealUpdate):
    existing = await prisma.deal.find_unique(where={"id": deal_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Deal not found")

    old_stage = existing.stage
    update_data = data.model_dump(exclude_unset=True, by_alias=True)
    rename_fields = {
        "expected_close_date": "expectedCloseDate",
    }
    for old_key, new_key in rename_fields.items():
        if old_key in update_data:
            update_data[new_key] = update_data.pop(old_key)

    deal = await prisma.deal.update(
        where={"id": deal_id},
        data=update_data,
    )
    deal = await prisma.deal.find_unique(
        where={"id": deal_id},
        include={"contact": True, "company": True},
    )

    if data.stage and data.stage != old_stage:
        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        contact = deal.contact
        await ga4_service.track_deal_stage_changed(
            client_id=generate_ga_client_id(),
            deal_id=deal.id,
            old_stage=str(old_stage) if hasattr(old_stage, "value") else str(old_stage),
            new_stage=data.stage,
            deal_value=deal.value,
            user_email=contact.email if contact else None,
        )

    return _prisma_to_dict(deal)


@router.delete("/{deal_id}")
async def delete_deal(deal_id: int):
    existing = await prisma.deal.find_unique(where={"id": deal_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Deal not found")
    await prisma.deal.delete(where={"id": deal_id})
    return {"deleted": True}


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _prisma_to_dict(obj) -> dict:
    """Convert Prisma model to dict, parsing JSON string fields and converting camelCase to snake_case recursively."""
    d = {}
    for key, value in obj.model_dump().items():
        snake_key = _camel_to_snake(key)
        if key in ("tags", "extra_data") and isinstance(value, str):
            try:
                d[snake_key] = json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                d[snake_key] = value if value else []
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