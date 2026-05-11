"""
Agents API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.models.models import Agent, AuditLog
from app.schemas.schemas import AgentCreate, AgentResponse, AgentUpdate

settings = get_settings()
router = APIRouter()


@router.get("/", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.id.desc()))
    return result.scalars().all()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(**data.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, data: AgentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
    return {"deleted": True}


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "paused"
    await db.commit()
    return {"agent_id": agent_id, "status": "paused"}


@router.post("/{agent_id}/resume")
async def resume_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "active"
    await db.commit()
    return {"agent_id": agent_id, "status": "active"}


@router.get("/{agent_id}/audit_log")
async def get_agent_audit_log(agent_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog).where(AuditLog.agent_id == agent_id)
        .order_by(AuditLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
