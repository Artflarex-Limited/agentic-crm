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
            lead_id=deal.lead_id if hasattr(deal, "lead_id") else None,
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
