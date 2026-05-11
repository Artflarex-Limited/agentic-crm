"""
Follow-up Agent
Manages snooze, auto-re-engage cold leads, schedules follow-ups.
"""
from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import Lead, Activity, AuditLog, ActivityType, LeadStage
from sqlalchemy import select
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="agents.follow_up.snooze_lead")
def snooze_lead(lead_id: int, snooze_until: datetime):
    """
    Snooze a lead until a future date.
    Lead will not be contacted during snooze period.
    """
    async def _snooze():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                return {"status": "error", "message": "Lead not found"}

            lead.snooze_until = snooze_until
            audit = AuditLog(
                action="lead_snoozed",
                entity_type="lead",
                entity_id=lead_id,
                details={"snooze_until": snooze_until.isoformat()},
            )
            db.add(audit)
            await db.commit()
            return {"status": "snoozed", "lead_id": lead_id, "snooze_until": snooze_until}

    return _run_async(_snooze())


@celery_app.task(name="agents.follow_up.process_cold_leads")
def process_cold_leads(days_threshold: int = 7):
    """
    Find leads that haven't been contacted in `days_threshold` days
    and re-engage them with follow-up actions.
    """
    async def _process_cold_leads():
        async with AsyncSessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days_threshold)
            result = await db.execute(
                select(Lead)
                .where(Lead.last_contacted_at < cutoff)
                .where(Lead.snooze_until < datetime.utcnow())
                .where(Lead.stage == LeadStage.NEW)
                .limit(50)
            )
            cold_leads = result.scalars().all()

            re_engaged = []
            for lead in cold_leads:
                activity = Activity(
                    lead_id=lead.id,
                    type=ActivityType.AGENT_ACTION,
                    content=f"Auto re-engagement: cold lead detected (last contact: {lead.last_contacted_at})",
                    metadata={"action": "re_engagement_check", "days_since_contact": days_threshold},
                )
                db.add(activity)
                lead.stage = LeadStage.CONTACTED
                re_engaged.append(lead.id)

            if re_engaged:
                audit = AuditLog(
                    action="cold_leads_re_engaged",
                    entity_type="lead",
                    entity_id=0,
                    details={"count": len(re_engaged), "lead_ids": re_engaged},
                )
                db.add(audit)
                await db.commit()

            return {"status": "processed", "count": len(re_engaged), "lead_ids": re_engaged}

    return _run_async(_process_cold_leads())


@celery_app.task(name="agents.follow_up.schedule_follow_up")
def schedule_follow_up(lead_id: int, follow_up_date: datetime, note: str = ""):
    """
    Schedule a follow-up for a specific date.
    Creates a pending activity to be picked up by relevant agent.
    """
    async def _schedule_follow_up():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                return {"status": "error", "message": "Lead not found"}

            activity = Activity(
                lead_id=lead_id,
                type=ActivityType.AGENT_ACTION,
                content=f"Scheduled follow-up: {note}",
                metadata={
                    "scheduled_for": follow_up_date.isoformat(),
                    "action": "scheduled_follow_up",
                },
            )
            db.add(activity)

            audit = AuditLog(
                action="follow_up_scheduled",
                entity_type="lead",
                entity_id=lead_id,
                details={"follow_up_date": follow_up_date.isoformat(), "note": note},
            )
            db.add(audit)
            await db.commit()
            return {"status": "scheduled", "lead_id": lead_id, "follow_up_date": follow_up_date}

    return _run_async(_schedule_follow_up())


def _run_async(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)