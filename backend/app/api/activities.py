"""
Activities API routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Activity
from app.schemas.schemas import ActivityCreate, ActivityResponse

router = APIRouter()


@router.get("/", response_model=list[ActivityResponse])
async def list_activities(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Activity).order_by(Activity.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=ActivityResponse, status_code=201)
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db)):
    activity = Activity(**data.model_dump())
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity
