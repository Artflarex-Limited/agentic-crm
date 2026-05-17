"""
RFQ Generation Agent
Automates RFQ processing, follow-ups, and value updates.
"""
import json
import logging
from datetime import datetime, timedelta

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole, LeadStage
from app.prisma import prisma
from app.services.rfq_service import get_rfq_service

logger = logging.getLogger(__name__)


async def generate_rfq_from_qualified_leads(min_score: int = 40, correlation_id: str | None = None):
    """
    Find qualified leads and automatically generate RFQs.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Generating RFQs from qualified leads: min_score={min_score}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        rfq_service = await get_rfq_service()

        leads = await prisma.lead.find_many(
            where={
                "score": {"gte": min_score},
                "stage": {"in": [LeadStage.CONTACTED.value, LeadStage.QUALIFIED.value]},
            },
            order={"score": "desc"},
            take=50,
        )

        generated = []
        for lead in leads:
            existing_deal = await prisma.deal.find_first(
                where={"contactId": lead.contactId}
            )
            if existing_deal:
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

        await prisma.auditlog.create(
            data={
                "action": "rfq_batch_generated",
                "entityType": "lead",
                "entityId": 0,
                "details": json.dumps({
                    "count": len(generated),
                    "min_score": min_score,
                    "rfqs": generated,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                }),
            }
        )

        logger.info(f"RFQ batch generated: {len(generated)} RFQs created", extra={"run_id": run_id})
        return {
            "status": "completed",
            "generated_count": len(generated),
            "rfqs": generated,
            "run_id": run_id,
        }
    except Exception as e:
        logger.error(f"Error generating RFQs: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}


async def update_stale_rfqs(days_threshold: int = 7, correlation_id: str | None = None):
    """
    Check for stale RFQs and trigger follow-up actions.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Updating stale RFQs: days_threshold={days_threshold}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        cutoff = datetime.utcnow() - timedelta(days=days_threshold)

        deals = await prisma.deal.find_many(
            where={
                "stage": {"in": ["LEAD", "QUALIFIED"]},
                "updatedAt": {"lt": cutoff.isoformat()},
            }
        )

        updated = []
        for deal in deals:
            await prisma.activity.create(
                data={
                    "dealId": deal.id,
                    "type": "AGENT_ACTION",
                    "content": f"RFQ follow-up: stale deal detected (updated {days_threshold}+ days ago)",
                    "activityMeta": json.dumps({
                        "action": "rfq_stale_check",
                        "days_since_update": days_threshold,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    }),
                }
            )
            updated.append(deal.id)

        if updated:
            await prisma.auditlog.create(
                data={
                    "action": "rfq_stale_updated",
                    "entityType": "deal",
                    "entityId": 0,
                    "details": json.dumps({
                        "count": len(updated),
                        "deal_ids": updated,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    }),
                }
            )

        logger.info(f"Stale RFQs updated: {len(updated)}", extra={"run_id": run_id})
        return {
            "status": "completed",
            "updated_count": len(updated),
            "deal_ids": updated,
            "run_id": run_id,
        }
    except Exception as e:
        logger.error(f"Error updating stale RFQs: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}


async def check_expiring_rfqs(days_before: int = 7, correlation_id: str | None = None):
    """
    Check for RFQs with expected close dates approaching.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.REPORTING)

    logger.info(
        f"Checking expiring RFQs: days_before={days_before}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        warning_date = datetime.utcnow() + timedelta(days=days_before)
        warning_start = datetime.utcnow() + timedelta(days=days_before - 1)

        deals = await prisma.deal.find_many(
            where={
                "stage": {"in": ["LEAD", "QUALIFIED", "PROPOSAL"]},
                "expectedCloseDate": {"not": None},
            }
        )

        expiring = []
        for deal in deals:
            if deal.expectedCloseDate:
                close_date = datetime.fromisoformat(deal.expectedCloseDate)
                if close_date <= warning_date and close_date >= warning_start:
                    days_until = (close_date - datetime.utcnow()).days
                    expiring.append({
                        "deal_id": deal.id,
                        "deal_name": deal.name,
                        "value": deal.value,
                        "expected_close_date": deal.expectedCloseDate,
                        "days_until": days_until,
                    })

        if expiring:
            await prisma.auditlog.create(
                data={
                    "action": "rfq_expiring_check",
                    "entityType": "deal",
                    "entityId": 0,
                    "details": json.dumps({
                        "count": len(expiring),
                        "deals": expiring,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    }),
                }
            )

        logger.info(f"Expiring RFQs found: {len(expiring)}", extra={"run_id": run_id})
        return {
            "status": "completed",
            "expiring_count": len(expiring),
            "deals": expiring,
            "run_id": run_id,
        }
    except Exception as e:
        logger.error(f"Error checking expiring RFQs: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}
