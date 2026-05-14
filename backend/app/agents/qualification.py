"""
Qualification Agent
Scores and routes leads, updates pipeline stages.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import Agent, AgentRole, AgentStatus, AuditLog, Lead, LeadStage
from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_run_id, get_current_correlation_id

logger = logging.getLogger(__name__)


@celery_app.task(
    name="agents.qualification.score_lead",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def score_lead(self, lead_id: int, correlation_id: str | None = None):
    """
    Score a lead based on available data.
    Updates lead score and may advance stage.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    ctx = AgentContext(role=AgentRole.QUALIFICATION)

    logger.info(
        f"Scoring lead: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _score_lead():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
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

            previous_stage = lead.stage.value if hasattr(lead.stage, 'value') else lead.stage
            lead.score = score
            lead.updated_at = datetime.utcnow()

            if score >= 40 and lead.stage == LeadStage.NEW:
                lead.stage = LeadStage.CONTACTED

            new_stage = lead.stage.value if hasattr(lead.stage, 'value') else lead.stage

            audit = AuditLog(
                action="lead_scored",
                entity_type="lead",
                entity_id=lead_id,
                details={
                    "score": score,
                    "previous_stage": previous_stage,
                    "new_stage": new_stage,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()
            logger.info(
                f"Lead scored: lead_id={lead_id}, score={score}, stage={new_stage}",
                extra={"run_id": run_id, "lead_id": lead_id, "score": score, "stage": new_stage}
            )
            return {"status": "scored", "lead_id": lead_id, "score": score, "stage": new_stage}

    return run_async(_score_lead())


@celery_app.task(
    name="agents.qualification.route_lead",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def route_lead(self, lead_id: int, correlation_id: str | None = None):
    """
    Route a qualified lead to appropriate agent or human.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    ctx = AgentContext(role=AgentRole.QUALIFICATION)

    logger.info(
        f"Routing lead: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _route_lead():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Lead not found"}

            target_role = AgentRole.OUTREACH if lead.score >= 50 else AgentRole.RESEARCH

            agent_result = await db.execute(
                select(Agent)
                .where(Agent.role == target_role)
                .where(Agent.status == AgentStatus.ACTIVE)
                .limit(1)
            )
            agent = agent_result.scalar_one_or_none()

            previous_agent_id = lead.assigned_agent_id
            if agent:
                lead.assigned_agent_id = agent.id

            audit = AuditLog(
                action="lead_routed",
                entity_type="lead",
                entity_id=lead_id,
                details={
                    "score": lead.score,
                    "previous_agent_id": previous_agent_id,
                    "assigned_agent_id": agent.id if agent else None,
                    "assigned_role": target_role.value if target_role else None,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()
            logger.info(
                f"Lead routed: lead_id={lead_id}, agent_id={agent.id if agent else None}, role={target_role.value}",
                extra={"run_id": run_id, "lead_id": lead_id, "agent_id": agent.id if agent else None}
            )
            return {
                "status": "routed",
                "lead_id": lead_id,
                "agent_id": agent.id if agent else None,
                "role": target_role.value,
            }

    return run_async(_route_lead())