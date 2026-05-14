"""
Lead Sourcing Agent
Finds and creates leads from LinkedIn, web forms, and cold outreach targets.
"""
import logging

from sqlalchemy import select

from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import AgentRole, AuditLog, Company, Contact, Lead, LeadSource
from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_run_id, get_current_correlation_id

logger = logging.getLogger(__name__)


@celery_app.task(name="agents.lead_sourcing.find_from_linkedin", bind=True, max_retries=3)
def find_leads_from_linkedin(self, query: str, limit: int = 10, correlation_id: str | None = None):
    """
    Search Apollo.io for LinkedIn prospects matching query.
    Returns list of contact dicts that get upserted into the DB.
    """
    from app.services.enrichment_service import EnrichmentService

    ctx = AgentContext(role=AgentRole.LEAD_SOURCING)
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()

    logger.info(
        f"Starting LinkedIn lead search: query={query}, limit={limit}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _find():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

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

            async with SessionLocal() as db:
                existing = await db.execute(
                    select(Contact).where(Contact.email == email)
                )
                contact = existing.scalar_one_or_none()

                if not contact:
                    company_data = contact_data.pop("company", {})
                    company = None
                    if company_data.get("name"):
                        company_result = await db.execute(
                            select(Company).where(Company.name == company_data["name"])
                        )
                        company = company_result.scalar_one_or_none()
                        if not company:
                            company = Company(name=company_data["name"])
                            db.add(company)
                            await db.flush()

                    contact_data["company_id"] = company.id if company else None
                    contact = Contact(**contact_data)
                    db.add(contact)
                    await db.flush()

                lead = Lead(
                    contact_id=contact.id,
                    source=LeadSource.COLD_OUTREACH,
                    score=contact_data.get("initial_score", 30),
                )
                db.add(lead)

                audit = AuditLog(
                    action="lead_created",
                    entity_type="lead",
                    entity_id=lead.id,
                    details={
                        "source": "lead_sourcing_agent",
                        "contact_email": email,
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)

                await db.commit()
                results.append({"lead_id": lead.id, "contact_id": contact.id})

        logger.info(
            f"LinkedIn search completed: created {len(results)} leads",
            extra={"run_id": run_id, "count": len(results)}
        )
        return {"status": "completed", "count": len(results), "results": results}

    return run_async(_find())


@celery_app.task(name="agents.lead_sourcing.upsert_lead", bind=True, max_retries=3)
def upsert_lead(self, contact_data: dict, correlation_id: str | None = None):
    """Upsert a lead from external source into DB"""
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    ctx = AgentContext(role=AgentRole.LEAD_SOURCING)

    logger.info(
        f"Starting lead upsert: email={contact_data.get('email')}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _upsert():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            email = contact_data.get("email")
            if email:
                existing = await db.execute(
                    select(Contact).where(Contact.email == email)
                )
                contact = existing.scalar_one_or_none()

            if not contact:
                company_data = contact_data.pop("company", {})
                company = None
                if company_data.get("name"):
                    company_result = await db.execute(
                        select(Company).where(Company.name == company_data["name"])
                    )
                    company = company_result.scalar_one_or_none()
                    if not company:
                        company = Company(name=company_data["name"])
                        db.add(company)
                        await db.flush()

                contact_data["company_id"] = company.id if company else None
                contact = Contact(**contact_data)
                db.add(contact)
                await db.flush()

            lead = Lead(
                contact_id=contact.id,
                source=LeadSource.COLD_OUTREACH,
                score=contact_data.get("initial_score", 30),
            )
            db.add(lead)

            audit = AuditLog(
                action="lead_created",
                entity_type="lead",
                entity_id=lead.id,
                details={
                    "source": "lead_sourcing_agent",
                    "contact_email": email,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)

            await db.commit()
            logger.info(
                f"Lead upserted: lead_id={lead.id}, contact_id={contact.id}",
                extra={"run_id": run_id}
            )
            return {"lead_id": lead.id, "contact_id": contact.id}

    return run_async(_upsert())