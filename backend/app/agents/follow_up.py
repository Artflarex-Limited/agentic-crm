"""
Follow-up Agent
Manages snooze, auto-re-engage cold leads, schedules follow-ups.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import Activity, ActivityType, AgentRole, AuditLog, Lead, LeadStage

logger = logging.getLogger(__name__)


@celery_app.task(
    name="agents.follow_up.snooze_lead",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def snooze_lead(self, lead_id: int, snooze_until: datetime, correlation_id: str | None = None):
    """
    Snooze a lead until a future date.
    Lead will not be contacted during snooze period.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.FOLLOW_UP)

    logger.info(
        f"Snoozing lead: lead_id={lead_id}, until={snooze_until}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _snooze():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Lead not found"}

            lead.snooze_until = snooze_until
            audit = AuditLog(
                action="lead_snoozed",
                entity_type="lead",
                entity_id=lead_id,
                details={
                    "snooze_until": snooze_until.isoformat(),
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()
            logger.info(
                f"Lead snoozed: lead_id={lead_id}, until={snooze_until}",
                extra={"run_id": run_id, "lead_id": lead_id}
            )
            return {"status": "snoozed", "lead_id": lead_id, "snooze_until": snooze_until}

    return run_async(_snooze())


@celery_app.task(
    name="agents.follow_up.process_cold_leads",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_cold_leads(self, days_threshold: int = 7, correlation_id: str | None = None):
    """
    Find leads that haven't been contacted in `days_threshold` days
    and re-engage them with follow-up actions.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.FOLLOW_UP)

    logger.info(
        f"Processing cold leads: days_threshold={days_threshold}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _process_cold_leads():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days_threshold)
            now = datetime.utcnow()

            result = await db.execute(
                select(Lead)
                .where(Lead.last_contacted_at < cutoff)
                .where(Lead.snooze_until.is_(None) | (Lead.snooze_until < now))
                .where(Lead.stage == LeadStage.NEW)
                .limit(50)
            )
            cold_leads = result.scalars().all()

            re_engaged = []
            for lead in cold_leads:
                last_contact = lead.last_contacted_at.isoformat() if lead.last_contacted_at else "never"
                activity = Activity(
                    lead_id=lead.id,
                    type=ActivityType.AGENT_ACTION,
                    content=f"Auto re-engagement: cold lead detected (last contact: {last_contact})",
                    activity_meta={
                        "action": "re_engagement_check",
                        "days_since_contact": days_threshold,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(activity)
                lead.stage = LeadStage.CONTACTED
                lead.last_contacted_at = datetime.utcnow()
                re_engaged.append(lead.id)

            if re_engaged:
                audit = AuditLog(
                    action="cold_leads_re_engaged",
                    entity_type="lead",
                    entity_id=0,
                    details={
                        "count": len(re_engaged),
                        "lead_ids": re_engaged,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)
                await db.commit()

            logger.info(
                f"Cold leads processed: re_engaged={len(re_engaged)}",
                extra={"run_id": run_id, "count": len(re_engaged)}
            )
            return {"status": "processed", "count": len(re_engaged), "lead_ids": re_engaged}

    return run_async(_process_cold_leads())


@celery_app.task(
    name="agents.follow_up.schedule_follow_up",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def schedule_follow_up(self, lead_id: int, follow_up_date: datetime, note: str = "", correlation_id: str | None = None):
    """
    Schedule a follow-up for a specific date.
    Creates a pending activity to be picked up by relevant agent.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.FOLLOW_UP)

    logger.info(
        f"Scheduling follow-up: lead_id={lead_id}, date={follow_up_date}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _schedule_follow_up():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Lead not found"}

            activity = Activity(
                lead_id=lead_id,
                type=ActivityType.AGENT_ACTION,
                content=f"Scheduled follow-up: {note}",
                activity_meta={
                    "scheduled_for": follow_up_date.isoformat(),
                    "action": "scheduled_follow_up",
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(activity)

            audit = AuditLog(
                action="follow_up_scheduled",
                entity_type="lead",
                entity_id=lead_id,
                details={
                    "follow_up_date": follow_up_date.isoformat(),
                    "note": note,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()
            logger.info(
                f"Follow-up scheduled: lead_id={lead_id}, date={follow_up_date}",
                extra={"run_id": run_id, "lead_id": lead_id}
            )
            return {"status": "scheduled", "lead_id": lead_id, "follow_up_date": follow_up_date}

    return run_async(_schedule_follow_up())
