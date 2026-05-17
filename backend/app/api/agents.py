"""
Agents API routes
"""
from fastapi import APIRouter, HTTPException

from app.prisma import prisma
from app.schemas.schemas import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter()


@router.get("/", response_model=list[AgentResponse])
async def list_agents():
    results = await prisma.agent.find_many(order=[{"id": "desc"}])
    return [r.model_dump() for r in results]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int):
    agent = await prisma.agent.find_first(where={"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.model_dump()


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate):
    agent = await prisma.agent.create(data=data.model_dump())
    return agent.model_dump()


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, data: AgentUpdate):
    agent = await prisma.agent.find_first(where={"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    update_data = data.model_dump(exclude_unset=True)
    agent = await prisma.agent.update(where={"id": agent_id}, data=update_data)
    return agent.model_dump()


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int):
    agent = await prisma.agent.find_first(where={"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await prisma.agent.delete(where={"id": agent_id})
    return {"deleted": True}


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: int):
    agent = await prisma.agent.find_first(where={"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = await prisma.agent.update(where={"id": agent_id}, data={"status": "paused"})
    return {"agent_id": agent_id, "status": "paused"}


@router.post("/{agent_id}/resume")
async def resume_agent(agent_id: int):
    agent = await prisma.agent.find_first(where={"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = await prisma.agent.update(where={"id": agent_id}, data={"status": "active"})
    return {"agent_id": agent_id, "status": "active"}


@router.get("/{agent_id}/audit_log")
async def get_agent_audit_log(agent_id: int, limit: int = 50):
    results = await prisma.auditlog.find_many(
        where={"agentId": agent_id},
        order=[{"createdAt": "desc"}],
        take=limit,
    )
    return [r.model_dump() for r in results]
