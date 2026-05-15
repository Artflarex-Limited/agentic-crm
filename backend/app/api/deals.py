"""
Deals API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.models import Deal
from app.schemas.schemas import DealCreate, DealResponse, DealUpdate
from app.services.rfq_service import get_rfq_service

router = APIRouter()


@router.get("/", response_model=list[DealResponse])
async def list_deals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deal).options(selectinload(Deal.contact), selectinload(Deal.company))
        .order_by(Deal.id.desc())
    )
    return result.scalars().all()


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
        .options(selectinload(Deal.contact), selectinload(Deal.company))
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("/", response_model=DealResponse, status_code=201)
async def create_deal(data: DealCreate, db: AsyncSession = Depends(get_db)):
    deal = Deal(**data.model_dump())
    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    if deal.value and deal.value > 0:
        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        contact = deal.contact
        await ga4_service.track_generate_rfq(
            client_id=generate_ga_client_id(),
            deal_id=deal.id,
            deal_value=deal.value,
            lead_id=deal.contact_id,
            user_email=contact.email if contact else None,
        )

    return deal


@router.post("/from-lead/{lead_id}", response_model=DealResponse, status_code=201)
async def create_rfq_from_lead(
    lead_id: int,
    deal_name: str | None = None,
    deal_value: float = 0.0,
    expected_close_days: int = 30,
    db: AsyncSession = Depends(get_db),
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

    deal_result = await db.execute(select(Deal).where(Deal.id == result["deal_id"]))
    deal = deal_result.scalar_one_or_none()
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

    return deal


@router.put("/{deal_id}/advance", response_model=DealResponse)
async def advance_rfq_stage(
    deal_id: int,
    target_stage: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Advance RFQ to next pipeline stage.
    """
    rfq_service = await get_rfq_service()
    success = await rfq_service.advance_rfq_stage(deal_id, target_stage)

    if not success:
        raise HTTPException(status_code=404, detail="Deal not found")

    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
        .options(selectinload(Deal.contact), selectinload(Deal.company))
    )
    deal = result.scalar_one_or_none()

    if deal and deal.value and deal.value > 0:
        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        contact = deal.contact
        await ga4_service.track_deal_stage_changed(
            client_id=generate_ga_client_id(),
            deal_id=deal.id,
            old_stage=str(deal.stage) if hasattr(deal.stage, 'value') else str(deal.stage),
            new_stage=target_stage,
            deal_value=deal.value,
            user_email=contact.email if contact else None,
        )

    return deal


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(deal_id: int, data: DealUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    old_stage = deal.stage
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(deal, key, value)
    await db.commit()
    await db.refresh(deal)

    if data.stage and data.stage != old_stage:
        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        contact = deal.contact
        await ga4_service.track_deal_stage_changed(
            client_id=generate_ga_client_id(),
            deal_id=deal.id,
            old_stage=old_stage,
            new_stage=data.stage,
            deal_value=deal.value,
            user_email=contact.email if contact else None,
        )

    return deal


@router.delete("/{deal_id}")
async def delete_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    await db.delete(deal)
    await db.commit()
    return {"deleted": True}
