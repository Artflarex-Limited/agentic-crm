"""
Qualification Agent
Scores and routes leads, updates pipeline stages.
"""
import json
import logging

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole, AgentStatus, LeadStage
from app.prisma import prisma

logger = logging.getLogger(__name__)


async def score_lead(lead_id: int, correlation_id: str | None = None):
    """
    Score a lead based on available data.
    Updates lead score and may advance stage.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.QUALIFICATION)

    logger.info(
        f"Scoring lead: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.qualification.score_lead"}
    )

    lead = await prisma.lead.find_unique(
        where={"id": lead_id},
        include={"contact": True}
    )
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

    previous_stage = lead.stage
    new_stage = lead.stage

    if score >= 40 and lead.stage == LeadStage.NEW.value:
        new_stage = LeadStage.CONTACTED.value

    update_data = {"score": score, "stage": new_stage}

    await prisma.lead.update(where={"id": lead_id}, data=update_data)

    details_json = json.dumps({
        "score": score,
        "previous_stage": previous_stage,
        "new_stage": new_stage,
        "run_id": run_id,
        "correlation_id": corr_id,
    })
    await prisma.auditlog.create(
        data={
            "action": "lead_scored",
            "entityType": "lead",
            "entityId": lead_id,
            "details": details_json,
        }
    )
    logger.info(
        f"Lead scored: lead_id={lead_id}, score={score}, stage={new_stage}",
        extra={"run_id": run_id, "lead_id": lead_id, "score": score, "stage": new_stage}
    )
    return {"status": "scored", "lead_id": lead_id, "score": score, "stage": new_stage}


async def route_lead(lead_id: int, correlation_id: str | None = None):
    """
    Route a qualified lead to appropriate agent or human.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.QUALIFICATION)

    logger.info(
        f"Routing lead: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.qualification.route_lead"}
    )

    lead = await prisma.lead.find_unique(
        where={"id": lead_id},
        include={"contact": True}
    )
    if not lead:
        logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
        return {"status": "error", "message": "Lead not found"}

    target_role = AgentRole.OUTREACH.value if lead.score >= 50 else AgentRole.RESEARCH.value

    agent = await prisma.agent.find_first(
        where={
            "role": target_role,
            "status": AgentStatus.ACTIVE.value,
        }
    )

    previous_agent_id = lead.assigned_agent_id
    update_data = {}
    if agent:
        update_data["assignedAgentId"] = agent.id
        await prisma.lead.update(where={"id": lead_id}, data=update_data)

    details_json = json.dumps({
        "score": lead.score,
        "previous_agent_id": previous_agent_id,
        "assigned_agent_id": agent.id if agent else None,
        "assigned_role": target_role,
        "run_id": run_id,
        "correlation_id": corr_id,
    })
    await prisma.auditlog.create(
        data={
            "action": "lead_routed",
            "entityType": "lead",
            "entityId": lead_id,
            "details": details_json,
        }
    )
    logger.info(
        f"Lead routed: lead_id={lead_id}, agent_id={agent.id if agent else None}, role={target_role}",
        extra={"run_id": run_id, "lead_id": lead_id, "agent_id": agent.id if agent else None}
    )
    return {
        "status": "routed",
        "lead_id": lead_id,
        "agent_id": agent.id if agent else None,
        "role": target_role,
    }
