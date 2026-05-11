"""
Qualification Agent
Scores and routes leads, updates pipeline stages.
"""
from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import Lead, Contact, Agent, AgentRole, AgentStatus, AuditLog, LeadStage
from sqlalchemy import select
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="agents.qualification.score_lead")
def score_lead(lead_id: int):
    """
    Score a lead based on available data.
    Updates lead score and may advance stage.
    """
    async def _score_lead():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                return {"status": "error", "message": "Lead not found"}

            contact = lead.contact
            score = 0

            if contact:
                if contact.email:
                    score += 10
                if contact.phone:
                    score += 15
                if contact.linkedin_url:
                    score += 15
                if contact.title:
                    score += 10
                if contact.company_id:
                    score += 10

            lead.score = score
            lead.updated_at = datetime.utcnow()

            if score >= 40 and lead.stage == LeadStage.NEW:
                lead.stage = LeadStage.CONTACTED

            audit = AuditLog(
                action="lead_scored",
                entity_type="lead",
                entity_id=lead_id,
                details={"score": score, "stage": lead.stage.value if hasattr(lead.stage, 'value') else lead.stage},
            )
            db.add(audit)
            await db.commit()
            return {"status": "scored", "lead_id": lead_id, "score": score}

    return _run_async(_score_lead())


@celery_app.task(name="agents.qualification.route_lead")
def route_lead(lead_id: int):
    """
    Route a qualified lead to appropriate agent or human.
    """
    async def _route_lead():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                return {"status": "error", "message": "Lead not found"}

            contact = lead.contact
            target_role = None

            if lead.score >= 50:
                target_role = AgentRole.OUTREACH
            else:
                target_role = AgentRole.RESEARCH

            agent_result = await db.execute(
                select(Agent)
                .where(Agent.role == target_role)
                .where(Agent.status == AgentStatus.ACTIVE)
                .limit(1)
            )
            agent = agent_result.scalar_one_or_none()

            if agent:
                lead.assigned_agent_id = agent.id

            audit = AuditLog(
                action="lead_routed",
                entity_type="lead",
                entity_id=lead_id,
                details={
                    "score": lead.score,
                    "assigned_agent_id": agent.id if agent else None,
                    "assigned_role": target_role.value if target_role else None,
                },
            )
            db.add(audit)
            await db.commit()
            return {
                "status": "routed",
                "lead_id": lead_id,
                "agent_id": agent.id if agent else None,
            }

    return _run_async(_route_lead())


def _run_async(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)