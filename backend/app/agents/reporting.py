"""
Reporting Agent
Daily summaries, pipeline alerts, stalled deal warnings.
"""
import json
import logging
from datetime import datetime, timedelta

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole, DealStage, LeadStage
from app.prisma import prisma

logger = logging.getLogger(__name__)


async def daily_summary(correlation_id: str | None = None) -> dict:
    """
    Generate daily summary of CRM activity.
    Returns stats and recent activity.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.REPORTING)

    logger.info(
        "Starting daily summary generation",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.reporting.daily_summary"}
    )

    today = datetime.utcnow().date()
    yesterday_start = datetime.combine(today - timedelta(days=1), datetime.min.time())
    today_start = datetime.combine(today, datetime.min.time())

    new_leads = await prisma.lead.count(
        where={
            "created_at": {
                "gte": yesterday_start.isoformat(),
                "lt": today_start.isoformat(),
            }
        }
    )

    new_deals = await prisma.deal.count(
        where={
            "created_at": {
                "gte": yesterday_start.isoformat(),
                "lt": today_start.isoformat(),
            }
        }
    )

    open_deals = await prisma.deal.count(
        where={
            "stage": {
                "in": [DealStage.LEAD.value, DealStage.QUALIFIED.value, DealStage.PROPOSAL.value]
            }
        }
    )

    recent_activities = await prisma.activity.find_many(
        where={
            "created_at": {
                "gte": yesterday_start.isoformat(),
            }
        },
        order={"created_at": "desc"},
        take=20,
    )

    summary = {
        "date": str(today - timedelta(days=1)),
        "new_leads": new_leads,
        "new_deals": new_deals,
        "open_deals": open_deals,
        "activities": [
            {
                "id": a.id,
                "type": a.type,
                "content": a.content,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_activities
        ],
        "run_id": run_id,
        "correlation_id": corr_id,
    }

    details_json = json.dumps({
        "date": summary["date"],
        "new_leads": new_leads,
        "new_deals": new_deals,
        "open_deals": open_deals,
        "activity_count": len(recent_activities),
        "run_id": run_id,
        "correlation_id": corr_id,
    })
    await prisma.auditlog.create(
        data={
            "action": "daily_summary_generated",
            "entityType": "report",
            "entityId": 0,
            "details": details_json,
        }
    )

    logger.info(
        f"Daily summary generated: {new_leads} leads, {new_deals} deals",
        extra={"run_id": run_id, "new_leads": new_leads, "new_deals": new_deals}
    )
    return summary


async def pipeline_alert(correlation_id: str | None = None) -> dict:
    """
    Check for stalled deals and send alerts.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.REPORTING)

    logger.info(
        "Starting pipeline alert check",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.reporting.pipeline_alert"}
    )

    cutoff = (datetime.utcnow() - timedelta(days=14)).isoformat()
    stalled_deals = await prisma.deal.find_many(
        where={
            "stage": {
                "in": [DealStage.LEAD.value, DealStage.QUALIFIED.value, DealStage.PROPOSAL.value]
            },
            "updated_at": {"lt": cutoff},
        }
    )

    alert_details = []
    for deal in stalled_deals:
        days_stalled = (datetime.utcnow() - deal.updated_at).days
        alert_details.append({
            "deal_id": deal.id,
            "deal_name": deal.name,
            "stage": deal.stage,
            "days_stalled": days_stalled,
        })

    if alert_details:
        details_json = json.dumps({
            "stalled_count": len(alert_details),
            "deals": alert_details,
            "run_id": run_id,
            "correlation_id": corr_id,
        })
        await prisma.auditlog.create(
            data={
                "action": "pipeline_alert",
                "entityType": "deal",
                "entityId": 0,
                "details": details_json,
            }
        )

    logger.info(
        f"Pipeline alert generated: {len(alert_details)} stalled deals",
        extra={"run_id": run_id, "stalled_count": len(alert_details)}
    )
    return {
        "status": "alert_generated",
        "stalled_deals": len(alert_details),
        "deals": alert_details,
        "run_id": run_id,
        "correlation_id": corr_id,
    }


async def stalled_lead_warning(days_threshold: int = 14, correlation_id: str | None = None) -> dict:
    """
    Find leads stuck in NEW stage for too long.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.REPORTING)

    logger.info(
        f"Starting stalled lead warning check: days_threshold={days_threshold}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.reporting.stalled_lead_warning"}
    )

    cutoff = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()
    stalled_leads = await prisma.lead.find_many(
        where={
            "stage": LeadStage.NEW.value,
            "created_at": {"lt": cutoff},
            "snooze_until": None,
        }
    )

    warnings = []
    for lead in stalled_leads:
        warnings.append({
            "lead_id": lead.id,
            "score": lead.score,
            "days_old": (datetime.utcnow() - lead.created_at).days,
        })

    details_json = json.dumps({
        "stalled_count": len(warnings),
        "leads": warnings,
        "days_threshold": days_threshold,
        "run_id": run_id,
        "correlation_id": corr_id,
    })
    await prisma.auditlog.create(
        data={
            "action": "stalled_lead_warning",
            "entityType": "lead",
            "entityId": 0,
            "details": details_json,
        }
    )

    logger.info(
        f"Stalled lead warning generated: {len(warnings)} stalled leads",
        extra={"run_id": run_id, "stalled_count": len(warnings)}
    )
    return {
        "status": "warning_generated",
        "stalled_leads": len(warnings),
        "leads": warnings,
        "run_id": run_id,
        "correlation_id": corr_id,
    }
