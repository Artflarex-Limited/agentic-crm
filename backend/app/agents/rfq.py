"""
RFQ Generation Agent
Automates RFQ processing, follow-ups, and value updates.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func

from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import Activity, ActivityType, AgentRole, AuditLog, Deal, DealStage, Lead, LeadStage
from app.services.rfq_service import get_rfq_service

logger = logging.getLogger(__name__)


@celery_app.task(
    name="agents.rfq.generate_from_qualified_leads",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_rfq_from_qualified_leads(self, min_score: int = 40, correlation_id: str | None = None):
    """
    Find qualified leads and automatically generate RFQs.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Generating RFQs from qualified leads: min_score={min_score}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _generate():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        rfq_service = await get_rfq_service()
        async with SessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.score >= min_score)
                .where(Lead.stage.in_([LeadStage.CONTACTED, LeadStage.QUALIFIED]))
                .order_by(Lead.score.desc())
                .limit(50)
            )
            leads = result.scalars().all()

            generated = []
            for lead in leads:
                existing_deal = await db.execute(
                    select(Deal).where(Deal.contact_id == lead.contact_id)
                )
                if existing_deal.scalar_one_or_none():
                    continue

                rfq_result = await rfq_service.create_rfq_from_lead(
                    lead_id=lead.id,
                    deal_value=float(lead.score * 100),
                    expected_close_days=30,
                )

                if rfq_result:
                    generated.append({
                        "lead_id": lead.id,
                        "deal_id": rfq_result["deal_id"],
                        "deal_value": rfq_result["deal_value"],
                    })

            audit = AuditLog(
                action="rfq_batch_generated",
                entity_type="lead",
                entity_id=0,
                details={
                    "count": len(generated),
                    "min_score": min_score,
                    "rfqs": generated,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(f"RFQ batch generated: {len(generated)} RFQs created", extra={"run_id": run_id})
            return {
                "status": "completed",
                "generated_count": len(generated),
                "rfqs": generated,
                "run_id": run_id,
            }

    return run_async(_generate())


@celery_app.task(
    name="agents.rfq.update_stale_rfqs",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def update_stale_rfqs(self, days_threshold: int = 7, correlation_id: str | None = None):
    """
    Check for stale RFQs and trigger follow-up actions.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Updating stale RFQs: days_threshold={days_threshold}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _update_stale():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days_threshold)

            result = await db.execute(
                select(Deal)
                .where(Deal.stage.in_([DealStage.LEAD, DealStage.QUALIFIED]))
                .where(Deal.updated_at < cutoff)
            )
            stale_deals = result.scalars().all()

            updated = []
            for deal in stale_deals:
                activity = Activity(
                    deal_id=deal.id,
                    type=ActivityType.AGENT_ACTION,
                    content=f"RFQ follow-up: stale deal detected (updated {days_threshold}+ days ago)",
                    activity_meta={
                        "action": "rfq_stale_check",
                        "days_since_update": days_threshold,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(activity)
                updated.append(deal.id)

            if updated:
                audit = AuditLog(
                    action="rfq_stale_updated",
                    entity_type="deal",
                    entity_id=0,
                    details={
                        "count": len(updated),
                        "deal_ids": updated,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)
                await db.commit()

            logger.info(f"Stale RFQs updated: {len(updated)}", extra={"run_id": run_id})
            return {
                "status": "completed",
                "updated_count": len(updated),
                "deal_ids": updated,
                "run_id": run_id,
            }

    return run_async(_update_stale())


@celery_app.task(
    name="agents.rfq.check_expiring_rfqs",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def check_expiring_rfqs(self, days_before: int = 7, correlation_id: str | None = None):
    """
    Check for RFQs with expected close dates approaching.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.REPORTING)

    logger.info(
        f"Checking expiring RFQs: days_before={days_before}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _check_expiring():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            warning_date = datetime.utcnow() + timedelta(days=days_before)
            warning_start = datetime.utcnow() + timedelta(days=days_before - 1)

            result = await db.execute(
                select(Deal)
                .where(Deal.stage.in_([DealStage.LEAD, DealStage.QUALIFIED, DealStage.PROPOSAL]))
                .where(Deal.expected_close_date.isnot(None))
                .where(Deal.expected_close_date <= warning_date)
                .where(Deal.expected_close_date >= warning_start)
            )
            expiring_deals = result.scalars().all()

            expiring = []
            for deal in expiring_deals:
                days_until = (deal.expected_close_date - datetime.utcnow()).days
                expiring.append({
                    "deal_id": deal.id,
                    "deal_name": deal.name,
                    "value": deal.value,
                    "expected_close_date": deal.expected_close_date.isoformat(),
                    "days_until": days_until,
                })

            if expiring:
                audit = AuditLog(
                    action="rfq_expiring_check",
                    entity_type="deal",
                    entity_id=0,
                    details={
                        "count": len(expiring),
                        "deals": expiring,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)
                await db.commit()

            logger.info(f"Expiring RFQs found: {len(expiring)}", extra={"run_id": run_id})
            return {
                "status": "completed",
                "expiring_count": len(expiring),
                "deals": expiring,
                "run_id": run_id,
            }

    return run_async(_check_expiring())