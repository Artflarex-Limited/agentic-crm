"""
Sequences API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import Sequence, SequenceEnrollment, Lead
from app.schemas.schemas import SequenceCreate, SequenceResponse

router = APIRouter()


@router.get("/", response_model=list[SequenceResponse])
async def list_sequences(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sequence).order_by(Sequence.id.desc()))
    return result.scalars().all()


@router.get("/{sequence_id}", response_model=SequenceResponse)
async def get_sequence(sequence_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sequence).where(Sequence.id == sequence_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return seq


@router.post("/", response_model=SequenceResponse, status_code=201)
async def create_sequence(data: SequenceCreate, db: AsyncSession = Depends(get_db)):
    seq = Sequence(**data.model_dump())
    db.add(seq)
    await db.commit()
    await db.refresh(seq)
    return seq


@router.put("/{sequence_id}", response_model=SequenceResponse)
async def update_sequence(sequence_id: int, data: SequenceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sequence).where(Sequence.id == sequence_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    for key, value in data.model_dump().items():
        setattr(seq, key, value)
    await db.commit()
    await db.refresh(seq)
    return seq


@router.delete("/{sequence_id}")
async def delete_sequence(sequence_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sequence).where(Sequence.id == sequence_id))
    seq = result.scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    await db.delete(seq)
    await db.commit()
    return {"deleted": True}


@router.post("/{sequence_id}/enroll/{lead_id}")
async def enroll_lead(sequence_id: int, lead_id: int, db: AsyncSession = Depends(get_db)):
    """Enroll a lead into a sequence"""
    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    enrollment = SequenceEnrollment(lead_id=lead_id, sequence_id=sequence_id)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return {"enrolled": True, "enrollment_id": enrollment.id}