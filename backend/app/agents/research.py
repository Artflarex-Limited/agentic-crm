"""
Research Agent
Enriches lead data from Apollo.io, company data lookups.
"""
import json
import logging

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models.models import AgentRole, AuditLog, Company, Lead
from app.prisma import prisma
from app.services.enrichment_service import EnrichmentService

logger = logging.getLogger(__name__)

enrichment_service = EnrichmentService()


async def enrich_lead(lead_id: int, correlation_id: str | None = None):
    """
    Enrich a lead with additional data from Apollo.io.
    Updates contact and company info.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.RESEARCH)

    logger.info(
        f"Starting lead enrichment: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.research.enrich_lead"}
    )

    lead = await prisma.lead.find_unique(
        where={"id": lead_id},
        include={"contact": True}
    )
    if not lead:
        logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
        return {"status": "error", "message": "Lead not found"}

    contact = lead.contact
    if not contact or not contact.email:
        logger.warning(f"Contact has no email for lead: {lead_id}", extra={"run_id": run_id})
        return {"status": "error", "message": "Contact has no email"}

    enriched = await enrichment_service.enrich_contact(contact.email)

    if enriched:
        extra_data = contact.extraData or {}
        merged_extra = {**extra_data, **enriched}
        extra_data_json = json.dumps(merged_extra)

        if enriched.get("company_name"):
            existing_company = await prisma.company.find_first(where={"name": enriched["company_name"]})
            if existing_company:
                company = existing_company
            else:
                company = await prisma.company.create(data={"name": enriched["company_name"]})
            await prisma.contact.update(
                where={"id": contact.id},
                data={"extraData": extra_data_json, "companyId": company.id}
            )
        else:
            await prisma.contact.update(
                where={"id": contact.id},
                data={"extraData": extra_data_json}
            )

        details_json = json.dumps({
            "source": "apollo",
            "fields_updated": list(enriched.keys()),
            "run_id": run_id,
            "correlation_id": corr_id,
        })
        await prisma.auditlog.create(
            data={
                "action": "lead_enriched",
                "entityType": "lead",
                "entityId": lead_id,
                "details": details_json,
            }
        )
        logger.info(
            f"Lead enriched: lead_id={lead_id}, fields={list(enriched.keys())}",
            extra={"run_id": run_id, "lead_id": lead_id, "fields": list(enriched.keys())}
        )
        return {"status": "enriched", "lead_id": lead_id, "fields": list(enriched.keys())}

    logger.info(f"No enrichment data found for lead: {lead_id}", extra={"run_id": run_id})
    return {"status": "no_data", "lead_id": lead_id}


async def enrich_company(company_id: int, correlation_id: str | None = None):
    """
    Enrich company data with additional info from Apollo.io.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.RESEARCH)

    logger.info(
        f"Starting company enrichment: company_id={company_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": "agents.research.enrich_company"}
    )

    company = await prisma.company.find_unique(where={"id": company_id})
    if not company:
        logger.warning(f"Company not found: {company_id}", extra={"run_id": run_id})
        return {"status": "error", "message": "Company not found"}

    enriched = await enrichment_service.enrich_company(company.name)

    if enriched:
        update_data = {}
        for key, value in enriched.items():
            if hasattr(company, key):
                update_data[key] = value

        if update_data:
            await prisma.company.update(where={"id": company_id}, data=update_data)

        details_json = json.dumps({
            "source": "apollo",
            "fields_updated": list(enriched.keys()),
            "run_id": run_id,
            "correlation_id": corr_id,
        })
        await prisma.auditlog.create(
            data={
                "action": "company_enriched",
                "entityType": "company",
                "entityId": company_id,
                "details": details_json,
            }
        )
        logger.info(
            f"Company enriched: company_id={company_id}, fields={list(enriched.keys())}",
            extra={"run_id": run_id, "company_id": company_id, "fields": list(enriched.keys())}
        )
        return {"status": "enriched", "company_id": company_id, "fields": list(enriched.keys())}

    logger.info(f"No enrichment data found for company: {company_id}", extra={"run_id": run_id})
    return {"status": "no_data", "company_id": company_id}