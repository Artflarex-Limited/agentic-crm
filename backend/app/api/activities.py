"""
Activities API routes
"""
import json

from fastapi import APIRouter, HTTPException

from app.prisma import prisma
from app.schemas.schemas import ActivityCreate, ActivityResponse

router = APIRouter()


@router.get("/", response_model=list[ActivityResponse])
async def list_activities(limit: int = 50):
    results = await prisma.activity.find_many(
        order=[{"createdAt": "desc"}],
        take=limit,
    )
    # Parse JSON metadata fields back to objects
    activities = []
    for r in results:
        data = r.model_dump()
        if data.get("metadata"):
            data["metadata"] = json.loads(data["metadata"])
        activities.append(data)
    return activities


@router.post("/", response_model=ActivityResponse, status_code=201)
async def create_activity(data: ActivityCreate):
    payload = data.model_dump()
    # Serialize JSON fields
    if payload.get("metadata"):
        payload["metadata"] = json.dumps(payload["metadata"])
    activity = await prisma.activity.create(data=payload)
    result_data = activity.model_dump()
    if result_data.get("metadata"):
        result_data["metadata"] = json.loads(result_data["metadata"])
    return result_data