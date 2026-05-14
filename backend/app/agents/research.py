"""
Research Agent
Enriches lead data from Apollo.io, company data lookups.
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import AgentRole, AuditLog, Company, Lead
from app.services.enrichment_service import EnrichmentService
from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_run_id, get_current_correlation_id

logger = logging.getLogger(__name__)


@celery_app.task(
    name="agents.research.enrich_lead",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def enrich_lead(self, lead_id: int, correlation_id: str | None = None):
    """
    Enrich a lead with additional data from Apollo.io.
    Updates contact and company info.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    ctx = AgentContext(role=AgentRole.RESEARCH)

    logger.info(
        f"Starting lead enrichment: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _enrich_lead():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Lead not found"}

            contact = lead.contact
            if not contact or not contact.email:
                logger.warning(f"Contact has no email for lead: {lead_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Contact has no email"}

            enriched = await enrichment_service.enrich_contact(contact.email)

            if enriched:
                if contact.extra_data is None:
                    contact.extra_data = {}
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
                    details={
                        "source": "apollo",
                        "fields_updated": list(enriched.keys()),
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)
                await db.commit()
                logger.info(
                    f"Lead enriched: lead_id={lead_id}, fields={list(enriched.keys())}",
                    extra={"run_id": run_id, "lead_id": lead_id, "fields": list(enriched.keys())}
                )
                return {"status": "enriched", "lead_id": lead_id, "fields": list(enriched.keys())}

            logger.info(f"No enrichment data found for lead: {lead_id}", extra={"run_id": run_id})
            return {"status": "no_data", "lead_id": lead_id}

    return run_async(_enrich_lead())


@celery_app.task(
    name="agents.research.enrich_company",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def enrich_company(self, company_id: int, correlation_id: str | None = None):
    """
    Enrich company data with additional info from Apollo.io.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    ctx = AgentContext(role=AgentRole.RESEARCH)

    logger.info(
        f"Starting company enrichment: company_id={company_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _enrich_company():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(select(Company).where(Company.id == company_id))
            company = result.scalar_one_or_none()
            if not company:
                logger.warning(f"Company not found: {company_id}", extra={"run_id": run_id})
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
                    details={
                        "source": "apollo",
                        "fields_updated": list(enriched.keys()),
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)
                await db.commit()
                logger.info(
                    f"Company enriched: company_id={company_id}, fields={list(enriched.keys())}",
                    extra={"run_id": run_id, "company_id": company_id, "fields": list(enriched.keys())}
                )
                return {"status": "enriched", "company_id": company_id, "fields": list(enriched.keys())}

            logger.info(f"No enrichment data found for company: {company_id}", extra={"run_id": run_id})
            return {"status": "no_data", "company_id": company_id}

    return run_async(_enrich_company())