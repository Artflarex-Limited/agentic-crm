"""
Leads API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.models import Lead
from app.schemas.schemas import LeadCreate, LeadResponse, LeadUpdate

router = APIRouter()


@router.get("/", response_model=list[LeadResponse])
async def list_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead).options(selectinload(Lead.contact)).order_by(Lead.id.desc())
    )
    return result.scalars().all()


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.contact))
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, data: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    await db.commit()
    return {"deleted": True}


@router.post("/{lead_id}/score")
async def rescore_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Recalculate lead score based on rules"""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Simple rule-based scoring
    score = 0
    contact = lead.contact
    if contact:
        if contact.email:
            score += 20
        if contact.phone:
            score += 20
        if contact.linkedin_url:
            score += 30

    lead.score = min(score, 100)
    await db.commit()
    await db.refresh(lead)
    return {"lead_id": lead_id, "new_score": lead.score}
