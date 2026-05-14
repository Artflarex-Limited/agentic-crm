"""
Research Agent
Enriches lead data from Apollo.io, company data lookups.
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import AuditLog, Company, Lead
from app.services.enrichment_service import EnrichmentService
from app.agents._async import run_async

logger = logging.getLogger(__name__)
enrichment_service = EnrichmentService()


@celery_app.task(name="agents.research.enrich_lead", bind=True, max_retries=3)
def enrich_lead(self, lead_id: int):
    """
    Enrich a lead with additional data from Apollo.io.
    Updates contact and company info.
    """
    async def _enrich_lead():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                return {"status": "error", "message": "Lead not found"}

            contact = lead.contact
            if not contact or not contact.email:
                return {"status": "error", "message": "Contact has no email"}

            enriched = await enrichment_service.enrich_contact(contact.email)

            if enriched:
                contact.extra_data = {**contact.extra_data, **enriched}
                if enriched.get("company_name"):
                    company_result = await db.execute(
                        select(Company).where(Company.name == enriched["company_name"])
                    )
                    company = company_result.scalar_one_or_none()
                    if not company:
                        company = Company(name=enriched["company_name"])
                        db.add(company)
                        await db.flush()
                    contact.company_id = company.id

                audit = AuditLog(
                    action="lead_enriched",
                    entity_type="lead",
                    entity_id=lead_id,
                    details={"source": "apollo", "fields_updated": list(enriched.keys())},
                )
                db.add(audit)
                await db.commit()
                return {"status": "enriched", "lead_id": lead_id, "fields": list(enriched.keys())}

            return {"status": "no_data", "lead_id": lead_id}

    return run_async(_enrich_lead())


@celery_app.task(name="agents.research.enrich_company", bind=True, max_retries=3)
def enrich_company(self, company_id: int):
    """
    Enrich company data with additional info from Apollo.io.
    """
    async def _enrich_company():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(select(Company).where(Company.id == company_id))
            company = result.scalar_one_or_none()
            if not company:
                return {"status": "error", "message": "Company not found"}

            enriched = await enrichment_service.enrich_company(company.name)

            if enriched:
                for key, value in enriched.items():
                    if hasattr(company, key):
                        setattr(company, key, value)

                audit = AuditLog(
                    action="company_enriched",
                    entity_type="company",
                    entity_id=company_id,
                    details={"source": "apollo", "fields_updated": list(enriched.keys())},
                )
                db.add(audit)
                await db.commit()
                return {"status": "enriched", "company_id": company_id, "fields": list(enriched.keys())}

            return {"status": "no_data", "company_id": company_id}

    return run_async(_enrich_company())