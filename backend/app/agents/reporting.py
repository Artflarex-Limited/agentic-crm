"""
Reporting Agent
Daily summaries, pipeline alerts, stalled deal warnings.
"""
from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import Lead, Deal, Activity, AuditLog, LeadStage, DealStage
from sqlalchemy import select, func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="agents.reporting.daily_summary")
def daily_summary() -> dict:
    """
    Generate daily summary of CRM activity.
    Returns stats and recent activity.
    """
    async def _daily_summary():
        async with AsyncSessionLocal() as db:
            today = datetime.utcnow().date()
            yesterday_start = datetime.combine(today - timedelta(days=1), datetime.min.time())
            today_start = datetime.combine(today, datetime.min.time())

            leads_count = await db.execute(
                select(func.count(Lead.id))
                .where(Lead.created_at >= yesterday_start)
                .where(Lead.created_at < today_start)
            )
            new_leads = leads_count.scalar() or 0

            deals_result = await db.execute(
                select(Deal)
                .where(Deal.created_at >= yesterday_start)
                .where(Deal.created_at < today_start)
            )
            new_deals = len(deals_result.scalars().all())

            pipeline_result = await db.execute(
                select(func.count(Deal.id)).where(Deal.stage.in_([DealStage.LEAD, DealStage.QUALIFIED, DealStage.PROPOSAL]))
            )
            open_deals = pipeline_result.scalar() or 0

            activities_result = await db.execute(
                select(Activity)
                .where(Activity.created_at >= yesterday_start)
                .order_by(Activity.created_at.desc())
                .limit(20)
            )
            recent_activities = activities_result.scalars().all()

            return {
                "date": str(today - timedelta(days=1)),
                "new_leads": new_leads,
                "new_deals": new_deals,
                "open_deals": open_deals,
                "activities": [
                    {
                        "id": a.id,
                        "type": a.type.value if hasattr(a.type, "value") else a.type,
                        "content": a.content,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in recent_activities
                ],
            }

    return _run_async(_daily_summary())


@celery_app.task(name="agents.reporting.pipeline_alert")
def pipeline_alert() -> dict:
    """
    Check for stalled deals and send alerts.
    """
    async def _pipeline_alert():
        async with AsyncSessionLocal() as db:
            stalled_result = await db.execute(
                select(Deal)
                .where(Deal.stage.in_([DealStage.LEAD, DealStage.QUALIFIED, DealStage.PROPOSAL]))
                .where(Deal.updated_at < datetime.utcnow() - timedelta(days=14))
            )
            stalled_deals = stalled_result.scalars().all()

            alert_details = []
            for deal in stalled_deals:
                alert_details.append({
                    "deal_id": deal.id,
                    "deal_name": deal.name,
                    "stage": deal.stage.value if hasattr(deal.stage, "value") else deal.stage,
                    "days_stalled": (datetime.utcnow() - deal.updated_at).days,
                })

            if alert_details:
                audit = AuditLog(
                    action="pipeline_alert",
                    entity_type="deal",
                    entity_id=0,
                    details={"stalled_count": len(alert_details), "deals": alert_details},
                )
                db.add(audit)
                await db.commit()

            return {
                "status": "alert_generated",
                "stalled_deals": len(alert_details),
                "deals": alert_details,
            }

    return _run_async(_pipeline_alert())


@celery_app.task(name="agents.reporting.stalled_lead_warning")
def stalled_lead_warning(days_threshold: int = 14) -> dict:
    """
    Find leads stuck in NEW stage for too long.
    """
    async def _stalled_lead_warning():
        async with AsyncSessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days_threshold)
            result = await db.execute(
                select(Lead)
                .where(Lead.stage == LeadStage.NEW)
                .where(Lead.created_at < cutoff)
                .where(Lead.snooze_until == None)
            )
            stalled_leads = result.scalars().all()

            warnings = []
            for lead in stalled_leads:
                warnings.append({
                    "lead_id": lead.id,
                    "score": lead.score,
                    "days_old": (datetime.utcnow() - lead.created_at).days,
                })

            return {
                "status": "warning_generated",
                "stalled_leads": len(warnings),
                "leads": warnings,
            }

    return _run_async(_stalled_lead_warning())


def _run_async(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)