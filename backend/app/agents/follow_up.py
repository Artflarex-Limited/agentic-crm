"""
Follow-up Agent
Manages snooze, auto-re-engage cold leads, schedules follow-ups.
"""
import json
import logging
from datetime import datetime, timedelta

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole
from app.prisma import prisma

logger = logging.getLogger(__name__)


async def snooze_lead(lead_id: int, snooze_until: datetime, correlation_id: str | None = None):
    """
    Snooze a lead until a future date.
    Lead will not be contacted during snooze period.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.FOLLOW_UP)

    logger.info(
        f"Snoozing lead: lead_id={lead_id}, until={snooze_until}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    lead = await prisma.lead.find_unique(where={"id": lead_id})
    if not lead:
        logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
        return {"status": "error", "message": "Lead not found"}

    await prisma.lead.update(
        where={"id": lead_id},
        data={"snooze_until": snooze_until}
    )

    await prisma.auditlog.create(
        data={
            "action": "lead_snoozed",
            "entity_type": "lead",
            "entity_id": lead_id,
            "details": json.dumps({
                "snooze_until": snooze_until.isoformat(),
                "run_id": run_id,
                "correlation_id": corr_id,
            })
        }
    )

    logger.info(
        f"Lead snoozed: lead_id={lead_id}, until={snooze_until}",
        extra={"run_id": run_id, "lead_id": lead_id}
    )
    return {"status": "snoozed", "lead_id": lead_id, "snooze_until": snooze_until}


async def process_cold_leads(days_threshold: int = 7, correlation_id: str | None = None):
    """
    Find leads that haven't been contacted in `days_threshold` days
    and re-engage them with follow-up actions.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.FOLLOW_UP)

    logger.info(
        f"Processing cold leads: days_threshold={days_threshold}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    now = datetime.utcnow()

    cold_leads = await prisma.lead.find_many(
        where={
            "last_contacted_at": {"lt": cutoff},
            "stage": "NEW",
            "OR": [
                {"snooze_until": None},
                {"snooze_until": {"lt": now}}
            ]
        },
        take=50
    )

    re_engaged = []
    for lead in cold_leads:
        last_contact = lead.last_contacted_at.isoformat() if lead.last_contacted_at else "never"
        await prisma.activity.create(
            data={
                "lead_id": lead.id,
                "type": "AGENT_ACTION",
                "content": f"Auto re-engagement: cold lead detected (last contact: {last_contact})",
                "activity_meta": json.dumps({
                    "action": "re_engagement_check",
                    "days_since_contact": days_threshold,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                })
            }
        )
        await prisma.lead.update(
            where={"id": lead.id},
            data={
                "stage": "CONTACTED",
                "last_contacted_at": datetime.utcnow()
            }
        )
        re_engaged.append(lead.id)

    if re_engaged:
        await prisma.auditlog.create(
            data={
                "action": "cold_leads_re_engaged",
                "entity_type": "lead",
                "entity_id": 0,
                "details": json.dumps({
                    "count": len(re_engaged),
                    "lead_ids": re_engaged,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                })
            }
        )

    logger.info(
        f"Cold leads processed: re_engaged={len(re_engaged)}",
        extra={"run_id": run_id, "count": len(re_engaged)}
    )
    return {"status": "processed", "count": len(re_engaged), "lead_ids": re_engaged}


async def schedule_follow_up(lead_id: int, follow_up_date: datetime, note: str = "", correlation_id: str | None = None):
    """
    Schedule a follow-up for a specific date.
    Creates a pending activity to be picked up by relevant agent.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.FOLLOW_UP)

    logger.info(
        f"Scheduling follow-up: lead_id={lead_id}, date={follow_up_date}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    lead = await prisma.lead.find_unique(where={"id": lead_id})
    if not lead:
        logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
        return {"status": "error", "message": "Lead not found"}

    await prisma.activity.create(
        data={
            "lead_id": lead_id,
            "type": "AGENT_ACTION",
            "content": f"Scheduled follow-up: {note}",
            "activity_meta": json.dumps({
                "scheduled_for": follow_up_date.isoformat(),
                "action": "scheduled_follow_up",
                "run_id": run_id,
                "correlation_id": corr_id,
            })
        }
    )

    await prisma.auditlog.create(
        data={
            "action": "follow_up_scheduled",
            "entity_type": "lead",
            "entity_id": lead_id,
            "details": json.dumps({
                "follow_up_date": follow_up_date.isoformat(),
                "note": note,
                "run_id": run_id,
                "correlation_id": corr_id,
            })
        }
    )

    logger.info(
        f"Follow-up scheduled: lead_id={lead_id}, date={follow_up_date}",
        extra={"run_id": run_id, "lead_id": lead_id}
    )
    return {"status": "scheduled", "lead_id": lead_id, "follow_up_date": follow_up_date}
