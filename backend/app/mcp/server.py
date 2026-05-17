"""
MCP Server for Agentic CRM

Provides Model Context Protocol interface for AI agents to interact with the CRM.
Exposes tools for lead management, contact operations, deal tracking, and agent actions.
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.database import AsyncSessionLocal
from app.models.models import (
    Activity,
    ActivityType,
    Agent,
    AgentRole,
    AgentStatus,
    AuditLog,
    Company,
    Contact,
    Deal,
    DealStage,
    Lead,
    LeadSource,
    LeadStage,
    Sequence,
    SequenceEnrollment,
)
from app.services.email_service import EmailService

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic CRM MCP Server", version="1.0.0")


class ToolCall(BaseModel):
    tool: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolResponse(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


async def execute_tool(tool: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Execute an MCP tool and return the result.
    """
    try:
        if tool == "create_lead":
            return await create_lead(parameters)
        elif tool == "get_lead":
            return await get_lead(parameters)
        elif tool == "update_lead":
            return await update_lead(parameters)
        elif tool == "list_leads":
            return await list_leads(parameters)
        elif tool == "score_lead":
            return await score_lead(parameters)
        elif tool == "create_contact":
            return await create_contact(parameters)
        elif tool == "get_contact":
            return await get_contact(parameters)
        elif tool == "update_contact":
            return await update_contact(parameters)
        elif tool == "list_contacts":
            return await list_contacts(parameters)
        elif tool == "create_deal":
            return await create_deal(parameters)
        elif tool == "get_deal":
            return await get_deal(parameters)
        elif tool == "update_deal":
            return await update_deal(parameters)
        elif tool == "list_deals":
            return await list_deals(parameters)
        elif tool == "create_company":
            return await create_company(parameters)
        elif tool == "get_company":
            return await get_company(parameters)
        elif tool == "update_company":
            return await update_company(parameters)
        elif tool == "list_companies":
            return await list_companies(parameters)
        elif tool == "create_activity":
            return await create_activity(parameters)
        elif tool == "list_activities":
            return await list_activities(parameters)
        elif tool == "enroll_in_sequence":
            return await enroll_in_sequence(parameters)
        elif tool == "send_email":
            return await send_email(parameters)
        elif tool == "get_agent_status":
            return await get_agent_status(parameters)
        elif tool == "pause_agent":
            return await pause_agent(parameters)
        elif tool == "resume_agent":
            return await resume_agent(parameters)
        elif tool == "get_pipeline_summary":
            return await get_pipeline_summary(parameters)
        elif tool == "search_records":
            return await search_records(parameters)
        else:
            return {"success": False, "error": f"Unknown tool: {tool}"}
    except Exception as e:
        logger.error(f"Tool execution error: {tool} - {e}")
        return {"success": False, "error": str(e)}


async def create_lead(params: dict[str, Any]) -> dict[str, Any]:
    """Create a new lead."""
    required = ["contact_id"]
    for field in required:
        if field not in params:
            return {"success": False, "error": f"Missing required field: {field}"}

    async with AsyncSessionLocal() as db:
        lead = Lead(
            contact_id=params["contact_id"],
            source=LeadSource(params.get("source", "other")),
            stage=LeadStage(params.get("stage", "new")),
            score=params.get("score", 0),
            tags=params.get("tags", []),
            notes=params.get("notes"),
            assigned_agent_id=params.get("assigned_agent_id"),
        )
        db.add(lead)
        await db.flush()

        audit = AuditLog(
            action="lead_created",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "mcp", "tool": "create_lead"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(lead)

        return {
            "success": True,
            "data": {
                "id": lead.id,
                "contact_id": lead.contact_id,
                "source": lead.source.value if hasattr(lead.source, "value") else lead.source,
                "stage": lead.stage.value if hasattr(lead.stage, "value") else lead.stage,
                "score": lead.score,
            },
        }


async def get_lead(params: dict[str, Any]) -> dict[str, Any]:
    """Get a lead by ID."""
    lead_id = params.get("lead_id")
    if not lead_id:
        return {"success": False, "error": "Missing required field: lead_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
            .options(selectinload(Lead.contact), selectinload(Lead.assigned_agent))
        )
        lead = result.scalar_one_or_none()
        if not lead:
            return {"success": False, "error": "Lead not found"}

        return {
            "success": True,
            "data": {
                "id": lead.id,
                "contact_id": lead.contact_id,
                "contact": {
                    "id": lead.contact.id,
                    "email": lead.contact.email,
                    "first_name": lead.contact.first_name,
                    "last_name": lead.contact.last_name,
                    "phone": lead.contact.phone,
                    "title": lead.contact.title,
                } if lead.contact else None,
                "source": lead.source.value if hasattr(lead.source, "value") else lead.source,
                "stage": lead.stage.value if hasattr(lead.stage, "value") else lead.stage,
                "score": lead.score,
                "tags": lead.tags,
                "notes": lead.notes,
                "assigned_agent": {
                    "id": lead.assigned_agent.id,
                    "name": lead.assigned_agent.name,
                    "role": lead.assigned_agent.role.value if hasattr(lead.assigned_agent.role, "value") else lead.assigned_agent.role,
                } if lead.assigned_agent else None,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            },
        }


async def update_lead(params: dict[str, Any]) -> dict[str, Any]:
    """Update a lead."""
    lead_id = params.get("lead_id")
    if not lead_id:
        return {"success": False, "error": "Missing required field: lead_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            return {"success": False, "error": "Lead not found"}

        updateable_fields = ["stage", "score", "tags", "notes", "assigned_agent_id", "snooze_until", "last_contacted_at"]
        for field in updateable_fields:
            if field in params:
                setattr(lead, field, params[field])

        lead.updated_at = datetime.utcnow()

        audit = AuditLog(
            action="lead_updated",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "mcp", "tool": "update_lead", "updates": {k: v for k, v in params.items() if k in updateable_fields}},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(lead)

        return {
            "success": True,
            "data": {
                "id": lead.id,
                "stage": lead.stage.value if hasattr(lead.stage, "value") else lead.stage,
                "score": lead.score,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            },
        }


async def list_leads(params: dict[str, Any]) -> dict[str, Any]:
    """List leads with optional filtering."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func

        query = select(Lead).options(selectinload(Lead.contact))
        if "stage" in params:
            query = query.where(Lead.stage == LeadStage(params["stage"]))
        if "source" in params:
            query = query.where(Lead.source == LeadSource(params["source"]))
        if "min_score" in params:
            query = query.where(Lead.score >= params["min_score"])
        if "assigned_agent_id" in params:
            query = query.where(Lead.assigned_agent_id == params["assigned_agent_id"])

        limit = params.get("limit", 50)
        offset = params.get("offset", 0)
        query = query.limit(limit).offset(offset).order_by(Lead.created_at.desc())

        result = await db.execute(query)
        leads = result.scalars().all()

        count_query = select(func.count(Lead.id))
        if "stage" in params:
            count_query = count_query.where(Lead.stage == LeadStage(params["stage"]))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        return {
            "success": True,
            "data": {
                "leads": [
                    {
                        "id": l.id,
                        "contact_id": l.contact_id,
                        "contact_email": l.contact.email if l.contact else None,
                        "source": l.source.value if hasattr(l.source, "value") else l.source,
                        "stage": l.stage.value if hasattr(l.stage, "value") else l.stage,
                        "score": l.score,
                        "created_at": l.created_at.isoformat() if l.created_at else None,
                    }
                    for l in leads
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }


async def score_lead(params: dict[str, Any]) -> dict[str, Any]:
    """Score a lead based on available data."""
    lead_id = params.get("lead_id")
    if not lead_id:
        return {"success": False, "error": "Missing required field: lead_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
            .options(selectinload(Lead.contact))
        )
        lead = result.scalar_one_or_none()
        if not lead:
            return {"success": False, "error": "Lead not found"}

        score = 0
        if lead.contact:
            if lead.contact.email:
                score += 10
            if lead.contact.phone:
                score += 15
            if lead.contact.linkedin_url:
                score += 15
            if lead.contact.title:
                score += 10
            if lead.contact.company_id:
                score += 10

        previous_stage = lead.stage.value if hasattr(lead.stage, "value") else lead.stage
        lead.score = score
        lead.updated_at = datetime.utcnow()

        if score >= 40 and lead.stage == LeadStage.NEW:
            lead.stage = LeadStage.CONTACTED

        new_stage = lead.stage.value if hasattr(lead.stage, "value") else lead.stage

        audit = AuditLog(
            action="lead_scored",
            entity_type="lead",
            entity_id=lead_id,
            details={"score": score, "previous_stage": previous_stage, "new_stage": new_stage, "source": "mcp"},
        )
        db.add(audit)
        await db.commit()

        return {
            "success": True,
            "data": {
                "lead_id": lead_id,
                "score": score,
                "previous_stage": previous_stage,
                "new_stage": new_stage,
            },
        }


async def create_contact(params: dict[str, Any]) -> dict[str, Any]:
    """Create a new contact."""
    required = ["email"]
    for field in required:
        if field not in params:
            return {"success": False, "error": f"Missing required field: {field}"}

    async with AsyncSessionLocal() as db:
        contact = Contact(
            email=params["email"],
            first_name=params.get("first_name"),
            last_name=params.get("last_name"),
            phone=params.get("phone"),
            title=params.get("title"),
            linkedin_url=params.get("linkedin_url"),
            company_id=params.get("company_id"),
            extra_data=params.get("extra_data", {}),
        )
        db.add(contact)
        await db.flush()

        audit = AuditLog(
            action="contact_created",
            entity_type="contact",
            entity_id=contact.id,
            details={"source": "mcp", "tool": "create_contact"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(contact)

        return {
            "success": True,
            "data": {
                "id": contact.id,
                "email": contact.email,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "phone": contact.phone,
                "title": contact.title,
            },
        }


async def get_contact(params: dict[str, Any]) -> dict[str, Any]:
    """Get a contact by ID."""
    contact_id = params.get("contact_id")
    if not contact_id:
        return {"success": False, "error": "Missing required field: contact_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Contact).where(Contact.id == contact_id))
        contact = result.scalar_one_or_none()
        if not contact:
            return {"success": False, "error": "Contact not found"}

        return {
            "success": True,
            "data": {
                "id": contact.id,
                "email": contact.email,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "phone": contact.phone,
                "title": contact.title,
                "linkedin_url": contact.linkedin_url,
                "company_id": contact.company_id,
                "extra_data": contact.extra_data,
            },
        }


async def update_contact(params: dict[str, Any]) -> dict[str, Any]:
    """Update a contact."""
    contact_id = params.get("contact_id")
    if not contact_id:
        return {"success": False, "error": "Missing required field: contact_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Contact).where(Contact.id == contact_id))
        contact = result.scalar_one_or_none()
        if not contact:
            return {"success": False, "error": "Contact not found"}

        updateable_fields = ["first_name", "last_name", "phone", "title", "linkedin_url", "company_id", "extra_data"]
        for field in updateable_fields:
            if field in params:
                setattr(contact, field, params[field])

        contact.updated_at = datetime.utcnow()

        audit = AuditLog(
            action="contact_updated",
            entity_type="contact",
            entity_id=contact.id,
            details={"source": "mcp", "tool": "update_contact"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(contact)

        return {
            "success": True,
            "data": {
                "id": contact.id,
                "email": contact.email,
                "first_name": contact.first_name,
                "updated_at": contact.updated_at.isoformat() if contact.updated_at else None,
            },
        }


async def list_contacts(params: dict[str, Any]) -> dict[str, Any]:
    """List contacts with optional filtering."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func

        query = select(Contact)
        if "company_id" in params:
            query = query.where(Contact.company_id == params["company_id"])
        if "email" in params:
            query = query.where(Contact.email == params["email"])

        limit = params.get("limit", 50)
        offset = params.get("offset", 0)
        query = query.limit(limit).offset(offset).order_by(Contact.created_at.desc())

        result = await db.execute(query)
        contacts = result.scalars().all()

        count_query = select(func.count(Contact.id))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        return {
            "success": True,
            "data": {
                "contacts": [
                    {
                        "id": c.id,
                        "email": c.email,
                        "first_name": c.first_name,
                        "last_name": c.last_name,
                        "phone": c.phone,
                        "title": c.title,
                    }
                    for c in contacts
                ],
                "total": total,
            },
        }


async def create_deal(params: dict[str, Any]) -> dict[str, Any]:
    """Create a new deal."""
    required = ["contact_id", "name"]
    for field in required:
        if field not in params:
            return {"success": False, "error": f"Missing required field: {field}"}

    async with AsyncSessionLocal() as db:
        deal = Deal(
            contact_id=params["contact_id"],
            name=params["name"],
            company_id=params.get("company_id"),
            value=params.get("value", 0.0),
            stage=DealStage(params.get("stage", "lead")),
            expected_close_date=params.get("expected_close_date"),
            notes=params.get("notes"),
        )
        db.add(deal)
        await db.flush()

        audit = AuditLog(
            action="deal_created",
            entity_type="deal",
            entity_id=deal.id,
            details={"source": "mcp", "tool": "create_deal"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(deal)

        return {
            "success": True,
            "data": {
                "id": deal.id,
                "name": deal.name,
                "stage": deal.stage.value if hasattr(deal.stage, "value") else deal.stage,
                "value": deal.value,
            },
        }


async def get_deal(params: dict[str, Any]) -> dict[str, Any]:
    """Get a deal by ID."""
    deal_id = params.get("deal_id")
    if not deal_id:
        return {"success": False, "error": "Missing required field: deal_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()
        if not deal:
            return {"success": False, "error": "Deal not found"}

        return {
            "success": True,
            "data": {
                "id": deal.id,
                "name": deal.name,
                "contact_id": deal.contact_id,
                "company_id": deal.company_id,
                "value": deal.value,
                "stage": deal.stage.value if hasattr(deal.stage, "value") else deal.stage,
                "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
                "notes": deal.notes,
            },
        }


async def update_deal(params: dict[str, Any]) -> dict[str, Any]:
    """Update a deal."""
    deal_id = params.get("deal_id")
    if not deal_id:
        return {"success": False, "error": "Missing required field: deal_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()
        if not deal:
            return {"success": False, "error": "Deal not found"}

        updateable_fields = ["name", "value", "stage", "expected_close_date", "actual_close_date", "notes"]
        for field in updateable_fields:
            if field in params:
                setattr(deal, field, params[field])

        deal.updated_at = datetime.utcnow()

        audit = AuditLog(
            action="deal_updated",
            entity_type="deal",
            entity_id=deal.id,
            details={"source": "mcp", "tool": "update_deal"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(deal)

        return {
            "success": True,
            "data": {
                "id": deal.id,
                "stage": deal.stage.value if hasattr(deal.stage, "value") else deal.stage,
                "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
            },
        }


async def list_deals(params: dict[str, Any]) -> dict[str, Any]:
    """List deals with optional filtering."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func

        query = select(Deal)
        if "stage" in params:
            query = query.where(Deal.stage == DealStage(params["stage"]))
        if "contact_id" in params:
            query = query.where(Deal.contact_id == params["contact_id"])

        limit = params.get("limit", 50)
        offset = params.get("offset", 0)
        query = query.limit(limit).offset(offset).order_by(Deal.created_at.desc())

        result = await db.execute(query)
        deals = result.scalars().all()

        count_query = select(func.count(Deal.id))
        if "stage" in params:
            count_query = count_query.where(Deal.stage == DealStage(params["stage"]))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        return {
            "success": True,
            "data": {
                "deals": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "value": d.value,
                        "stage": d.stage.value if hasattr(d.stage, "value") else d.stage,
                    }
                    for d in deals
                ],
                "total": total,
            },
        }


async def create_company(params: dict[str, Any]) -> dict[str, Any]:
    """Create a new company."""
    name = params.get("name")
    if not name:
        return {"success": False, "error": "Missing required field: name"}

    async with AsyncSessionLocal() as db:
        company = Company(
            name=name,
            domain=params.get("domain"),
            industry=params.get("industry"),
            size=params.get("size"),
            linkedin_url=params.get("linkedin_url"),
            extra_data=params.get("extra_data", {}),
        )
        db.add(company)
        await db.flush()

        audit = AuditLog(
            action="company_created",
            entity_type="company",
            entity_id=company.id,
            details={"source": "mcp", "tool": "create_company"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(company)

        return {
            "success": True,
            "data": {
                "id": company.id,
                "name": company.name,
                "domain": company.domain,
                "industry": company.industry,
            },
        }


async def get_company(params: dict[str, Any]) -> dict[str, Any]:
    """Get a company by ID."""
    company_id = params.get("company_id")
    if not company_id:
        return {"success": False, "error": "Missing required field: company_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            return {"success": False, "error": "Company not found"}

        return {
            "success": True,
            "data": {
                "id": company.id,
                "name": company.name,
                "domain": company.domain,
                "industry": company.industry,
                "size": company.size,
                "linkedin_url": company.linkedin_url,
                "extra_data": company.extra_data,
            },
        }


async def update_company(params: dict[str, Any]) -> dict[str, Any]:
    """Update a company."""
    company_id = params.get("company_id")
    if not company_id:
        return {"success": False, "error": "Missing required field: company_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            return {"success": False, "error": "Company not found"}

        updateable_fields = ["name", "domain", "industry", "size", "linkedin_url", "extra_data"]
        for field in updateable_fields:
            if field in params:
                setattr(company, field, params[field])

        company.updated_at = datetime.utcnow()

        audit = AuditLog(
            action="company_updated",
            entity_type="company",
            entity_id=company.id,
            details={"source": "mcp", "tool": "update_company"},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(company)

        return {
            "success": True,
            "data": {
                "id": company.id,
                "name": company.name,
                "updated_at": company.updated_at.isoformat() if company.updated_at else None,
            },
        }


async def list_companies(params: dict[str, Any]) -> dict[str, Any]:
    """List companies with optional filtering."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func

        query = select(Company)
        if "industry" in params:
            query = query.where(Company.industry == params["industry"])

        limit = params.get("limit", 50)
        offset = params.get("offset", 0)
        query = query.limit(limit).offset(offset).order_by(Company.created_at.desc())

        result = await db.execute(query)
        companies = result.scalars().all()

        count_query = select(func.count(Company.id))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        return {
            "success": True,
            "data": {
                "companies": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "domain": c.domain,
                        "industry": c.industry,
                    }
                    for c in companies
                ],
                "total": total,
            },
        }


async def create_activity(params: dict[str, Any]) -> dict[str, Any]:
    """Create a new activity."""
    required = ["type"]
    for field in required:
        if field not in params:
            return {"success": False, "error": f"Missing required field: {field}"}

    async with AsyncSessionLocal() as db:
        activity = Activity(
            lead_id=params.get("lead_id"),
            contact_id=params.get("contact_id"),
            deal_id=params.get("deal_id"),
            agent_id=params.get("agent_id"),
            type=ActivityType(params["type"]),
            content=params.get("content"),
            activity_meta=params.get("metadata", {}),
        )
        db.add(activity)
        await db.flush()

        audit = AuditLog(
            action="activity_created",
            entity_type="activity",
            entity_id=activity.id,
            details={"source": "mcp", "tool": "create_activity", "type": params["type"]},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(activity)

        return {
            "success": True,
            "data": {
                "id": activity.id,
                "type": activity.type.value if hasattr(activity.type, "value") else activity.type,
                "content": activity.content,
            },
        }


async def list_activities(params: dict[str, Any]) -> dict[str, Any]:
    """List activities with optional filtering."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        query = select(Activity)
        if "lead_id" in params:
            query = query.where(Activity.lead_id == params["lead_id"])
        if "contact_id" in params:
            query = query.where(Activity.contact_id == params["contact_id"])
        if "deal_id" in params:
            query = query.where(Activity.deal_id == params["deal_id"])
        if "type" in params:
            query = query.where(Activity.type == ActivityType(params["type"]))

        limit = params.get("limit", 50)
        offset = params.get("offset", 0)
        query = query.limit(limit).offset(offset).order_by(Activity.created_at.desc())

        result = await db.execute(query)
        activities = result.scalars().all()

        return {
            "success": True,
            "data": {
                "activities": [
                    {
                        "id": a.id,
                        "type": a.type.value if hasattr(a.type, "value") else a.type,
                        "content": a.content,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in activities
                ],
            },
        }


async def enroll_in_sequence(params: dict[str, Any]) -> dict[str, Any]:
    """Enroll a lead in an email sequence."""
    lead_id = params.get("lead_id")
    sequence_id = params.get("sequence_id")
    if not lead_id or not sequence_id:
        return {"success": False, "error": "Missing required fields: lead_id, sequence_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        existing = await db.execute(
            select(SequenceEnrollment)
            .where(SequenceEnrollment.lead_id == lead_id)
            .where(SequenceEnrollment.sequence_id == sequence_id)
        )
        enrollment = existing.scalar_one_or_none()
        if enrollment:
            return {"success": True, "data": {"status": "already_enrolled", "enrollment_id": enrollment.id}}

        enrollment = SequenceEnrollment(
            lead_id=lead_id,
            sequence_id=sequence_id,
            current_step=0,
            status="active",
            enrolled_at=datetime.utcnow(),
        )
        db.add(enrollment)
        await db.flush()

        audit = AuditLog(
            action="sequence_enrolled",
            entity_type="lead",
            entity_id=lead_id,
            details={"sequence_id": sequence_id, "source": "mcp"},
        )
        db.add(audit)
        await db.commit()

        return {
            "success": True,
            "data": {
                "status": "enrolled",
                "enrollment_id": enrollment.id,
                "lead_id": lead_id,
                "sequence_id": sequence_id,
            },
        }


async def send_email(params: dict[str, Any]) -> dict[str, Any]:
    """Send an email to a contact."""
    to_email = params.get("to_email")
    subject = params.get("subject")
    body = params.get("body")
    if not to_email or not subject or not body:
        return {"success": False, "error": "Missing required fields: to_email, subject, body"}

    email_service = EmailService()
    sent = await email_service.send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        from_email=params.get("from_email"),
        html=params.get("html", False),
    )

    if sent:
        return {"success": True, "data": {"status": "sent", "to": to_email}}
    else:
        return {"success": False, "error": "Failed to send email"}


async def get_agent_status(params: dict[str, Any]) -> dict[str, Any]:
    """Get status of an agent or all agents."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        if "agent_id" in params:
            result = await db.execute(select(Agent).where(Agent.id == params["agent_id"]))
            agent = result.scalar_one_or_none()
            if not agent:
                return {"success": False, "error": "Agent not found"}
            agents = [agent]
        else:
            result = await db.execute(select(Agent))
            agents = result.scalars().all()

        return {
            "success": True,
            "data": {
                "agents": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "role": a.role.value if hasattr(a.role, "value") else a.role,
                        "status": a.status.value if hasattr(a.status, "value") else a.status,
                        "config": a.config,
                    }
                    for a in agents
                ]
            },
        }


async def pause_agent(params: dict[str, Any]) -> dict[str, Any]:
    """Pause an agent."""
    agent_id = params.get("agent_id")
    if not agent_id:
        return {"success": False, "error": "Missing required field: agent_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            return {"success": False, "error": "Agent not found"}

        agent.status = AgentStatus.PAUSED
        agent.updated_at = datetime.utcnow()

        audit = AuditLog(
            action="agent_paused",
            entity_type="agent",
            entity_id=agent_id,
            details={"source": "mcp"},
        )
        db.add(audit)
        await db.commit()

        return {"success": True, "data": {"agent_id": agent_id, "status": "paused"}}


async def resume_agent(params: dict[str, Any]) -> dict[str, Any]:
    """Resume a paused agent."""
    agent_id = params.get("agent_id")
    if not agent_id:
        return {"success": False, "error": "Missing required field: agent_id"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            return {"success": False, "error": "Agent not found"}

        agent.status = AgentStatus.ACTIVE
        agent.updated_at = datetime.utcnow()

        audit = AuditLog(
            action="agent_resumed",
            entity_type="agent",
            entity_id=agent_id,
            details={"source": "mcp"},
        )
        db.add(audit)
        await db.commit()

        return {"success": True, "data": {"agent_id": agent_id, "status": "active"}}


async def get_pipeline_summary(params: dict[str, Any]) -> dict[str, Any]:
    """Get pipeline summary with deal stages and values."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import func, select

        stages = ["lead", "qualified", "proposal", "negotiation", "won", "lost"]
        summary = {}
        total_value = 0.0

        for stage in stages:
            result = await db.execute(
                select(func.count(Deal.id), func.coalesce(func.sum(Deal.value), 0))
                .where(Deal.stage == DealStage(stage))
            )
            row = result.one()
            count = row[0] or 0
            value = float(row[1] or 0)
            summary[stage] = {"count": count, "value": value}
            if stage not in ["won", "lost"]:
                total_value += value

        return {
            "success": True,
            "data": {
                "stages": summary,
                "total_pipeline_value": total_value,
            },
        }


async def search_records(params: dict[str, Any]) -> dict[str, Any]:
    """Search across leads, contacts, and companies."""
    query = params.get("query", "")
    if not query:
        return {"success": False, "error": "Missing required field: query"}

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, or_

        lead_results = await db.execute(
            select(Lead)
            .where(
                or_(
                    Lead.notes.ilike(f"%{query}%"),
                    Lead.tags.ilike(f"%{query}%"),
                )
            )
            .limit(10)
        )
        leads = lead_results.scalars().all()

        contact_results = await db.execute(
            select(Contact)
            .where(
                or_(
                    Contact.email.ilike(f"%{query}%"),
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.phone.ilike(f"%{query}%"),
                )
            )
            .limit(10)
        )
        contacts = contact_results.scalars().all()

        company_results = await db.execute(
            select(Company)
            .where(
                or_(
                    Company.name.ilike(f"%{query}%"),
                    Company.domain.ilike(f"%{query}%"),
                )
            )
            .limit(10)
        )
        companies = company_results.scalars().all()

        return {
            "success": True,
            "data": {
                "leads": [
                    {"id": l.id, "score": l.score, "stage": l.stage.value if hasattr(l.stage, "value") else l.stage}
                    for l in leads
                ],
                "contacts": [
                    {"id": c.id, "email": c.email, "name": f"{c.first_name or ''} {c.last_name or ''}".strip()}
                    for c in contacts
                ],
                "companies": [
                    {"id": co.id, "name": co.name, "domain": co.domain}
                    for co in companies
                ],
            },
        }


@app.post("/mcp/execute")
async def execute_mcp_tool(tool_call: ToolCall) -> ToolResponse:
    """
    Execute an MCP tool call.

    MCP (Model Context Protocol) provides a standardized interface for AI agents
    to interact with the CRM. Each tool wraps a CRM operation.
    """
    logger.info(f"MCP tool call: {tool_call.tool}")
    result = await execute_tool(tool_call.tool, tool_call.parameters)
    return ToolResponse(
        success=result.get("success", False),
        data=result.get("data"),
        error=result.get("error"),
    )


@app.get("/mcp/tools")
async def list_mcp_tools():
    """
    List all available MCP tools.
    """
    return {
        "tools": [
            {"name": "create_lead", "description": "Create a new lead", "parameters": ["contact_id", "source", "stage", "score", "tags", "notes"]},
            {"name": "get_lead", "description": "Get a lead by ID", "parameters": ["lead_id"]},
            {"name": "update_lead", "description": "Update a lead", "parameters": ["lead_id", "stage", "score", "tags", "notes", "assigned_agent_id"]},
            {"name": "list_leads", "description": "List leads with filters", "parameters": ["stage", "source", "min_score", "limit", "offset"]},
            {"name": "score_lead", "description": "Score a lead based on available data", "parameters": ["lead_id"]},
            {"name": "create_contact", "description": "Create a new contact", "parameters": ["email", "first_name", "last_name", "phone", "title", "linkedin_url", "company_id"]},
            {"name": "get_contact", "description": "Get a contact by ID", "parameters": ["contact_id"]},
            {"name": "update_contact", "description": "Update a contact", "parameters": ["contact_id", "first_name", "last_name", "phone", "title", "linkedin_url", "company_id"]},
            {"name": "list_contacts", "description": "List contacts with filters", "parameters": ["company_id", "email", "limit", "offset"]},
            {"name": "create_deal", "description": "Create a new deal", "parameters": ["contact_id", "name", "company_id", "value", "stage", "expected_close_date", "notes"]},
            {"name": "get_deal", "description": "Get a deal by ID", "parameters": ["deal_id"]},
            {"name": "update_deal", "description": "Update a deal", "parameters": ["deal_id", "name", "value", "stage", "expected_close_date", "notes"]},
            {"name": "list_deals", "description": "List deals with filters", "parameters": ["stage", "contact_id", "limit", "offset"]},
            {"name": "create_company", "description": "Create a new company", "parameters": ["name", "domain", "industry", "size", "linkedin_url"]},
            {"name": "get_company", "description": "Get a company by ID", "parameters": ["company_id"]},
            {"name": "update_company", "description": "Update a company", "parameters": ["company_id", "name", "domain", "industry", "size", "linkedin_url"]},
            {"name": "list_companies", "description": "List companies with filters", "parameters": ["industry", "limit", "offset"]},
            {"name": "create_activity", "description": "Create a new activity", "parameters": ["type", "lead_id", "contact_id", "deal_id", "agent_id", "content", "metadata"]},
            {"name": "list_activities", "description": "List activities with filters", "parameters": ["lead_id", "contact_id", "deal_id", "type", "limit", "offset"]},
            {"name": "enroll_in_sequence", "description": "Enroll a lead in an email sequence", "parameters": ["lead_id", "sequence_id"]},
            {"name": "send_email", "description": "Send an email", "parameters": ["to_email", "subject", "body", "from_email", "html"]},
            {"name": "get_agent_status", "description": "Get agent status", "parameters": ["agent_id (optional)"]},
            {"name": "pause_agent", "description": "Pause an agent", "parameters": ["agent_id"]},
            {"name": "resume_agent", "description": "Resume a paused agent", "parameters": ["agent_id"]},
            {"name": "get_pipeline_summary", "description": "Get pipeline summary with deal stages and values", "parameters": []},
            {"name": "search_records", "description": "Search across leads, contacts, and companies", "parameters": ["query"]},
        ]
    }


@app.get("/health")
async def mcp_health():
    return {"status": "healthy", "service": "mcp-server", "version": "1.0.0"}