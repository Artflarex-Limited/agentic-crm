"""
Lead Sourcing Agent
Finds and creates leads from LinkedIn, web forms, and cold outreach targets.
"""
import json
import logging

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole, LeadSource
from app.prisma import prisma
from app.services.enrichment_service import EnrichmentService

logger = logging.getLogger(__name__)


async def find_leads_from_linkedin(query: str, limit: int = 10, correlation_id: str | None = None):
    """
    Search Apollo.io for LinkedIn prospects matching query.
    Returns list of contact dicts that get upserted into the DB.
    """
    AgentContext(role=AgentRole.LEAD_SOURCING)
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()

    logger.info(
        f"Starting LinkedIn lead search: query={query}, limit={limit}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.lead_sourcing.find_from_linkedin"}
    )

    enrichment_service = EnrichmentService()
    contacts = await enrichment_service.search_contacts(query, limit=limit)

    if not contacts:
        logger.info(f"No contacts found for query: {query}", extra={"run_id": run_id})
        return {"status": "completed", "count": 0, "results": []}

    results = []
    for contact_data in contacts:
        email = contact_data.get("email")
        if not email:
            continue

        existing_contact = await prisma.contact.find_first(where={"email": email})

        if not existing_contact:
            company_data = contact_data.pop("company", {})
            company = None
            if company_data.get("name"):
                existing_company = await prisma.company.find_first(where={"name": company_data["name"]})
                if existing_company:
                    company = existing_company
                else:
                    company = await prisma.company.create(data={"name": company_data["name"]})

            contact_data["companyId"] = company.id if company else None
            contact = await prisma.contact.create(data=contact_data)
        else:
            contact = existing_contact

        lead = await prisma.lead.create(
            data={
                "contactId": contact.id,
                "source": LeadSource.COLD_OUTREACH.value,
                "score": contact_data.get("initial_score", 30),
            }
        )

        details_json = json.dumps({
            "source": "lead_sourcing_agent",
            "contact_email": email,
            "run_id": run_id,
            "correlation_id": corr_id,
        })
        await prisma.auditlog.create(
            data={
                "action": "lead_created",
                "entityType": "lead",
                "entityId": lead.id,
                "details": details_json,
            }
        )

        results.append({"lead_id": lead.id, "contact_id": contact.id})

    logger.info(
        f"LinkedIn search completed: created {len(results)} leads",
        extra={"run_id": run_id, "count": len(results)}
    )
    return {"status": "completed", "count": len(results), "results": results}


async def upsert_lead(contact_data: dict, correlation_id: str | None = None):
    """Upsert a lead from external source into DB"""
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.LEAD_SOURCING)

    logger.info(
        f"Starting lead upsert: email={contact_data.get('email')}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.lead_sourcing.upsert_lead"}
    )

    email = contact_data.get("email")
    existing_contact = await prisma.contact.find_first(where={"email": email}) if email else None

    if not existing_contact:
        company_data = contact_data.pop("company", {})
        company = None
        if company_data.get("name"):
            existing_company = await prisma.company.find_first(where={"name": company_data["name"]})
            if existing_company:
                company = existing_company
            else:
                company = await prisma.company.create(data={"name": company_data["name"]})

        contact_data["companyId"] = company.id if company else None
        contact = await prisma.contact.create(data=contact_data)
    else:
        contact = existing_contact

    lead = await prisma.lead.create(
        data={
            "contactId": contact.id,
            "source": LeadSource.COLD_OUTREACH.value,
            "score": contact_data.get("initial_score", 30),
        }
    )

    details_json = json.dumps({
        "source": "lead_sourcing_agent",
        "contact_email": email,
        "run_id": run_id,
        "correlation_id": corr_id,
    })
    await prisma.auditlog.create(
        data={
            "action": "lead_created",
            "entityType": "lead",
            "entityId": lead.id,
            "details": details_json,
        }
    )

    logger.info(
        f"Lead upserted: lead_id={lead.id}, contact_id={contact.id}",
        extra={"run_id": run_id}
    )
    return {"lead_id": lead.id, "contact_id": contact.id}