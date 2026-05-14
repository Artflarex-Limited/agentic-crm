"""
Lead Sourcing Agent
Finds and creates leads from LinkedIn, web forms, and cold outreach targets.
"""
import logging

from sqlalchemy import select

from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import AuditLog, Company, Contact, Lead, LeadSource
from app.agents._async import run_async

logger = logging.getLogger(__name__)


@celery_app.task(name="agents.lead_sourcing.find_from_linkedin", bind=True, max_retries=3)
def find_leads_from_linkedin(self, query: str, limit: int = 10):
    """
    Search Apollo.io for LinkedIn prospects matching query.
    Returns list of contact dicts that get upserted into the DB.
    """
    from app.services.enrichment_service import EnrichmentService

    async def _find():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
            return {"status": "error", "message": "Database not configured"}

        enrichment_service = EnrichmentService()
        contacts = await enrichment_service.search_contacts(query, limit=limit)

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
                    details={"source": "lead_sourcing_agent", "contact_email": email},
                )
                db.add(audit)

                await db.commit()
                results.append({"lead_id": lead.id, "contact_id": contact.id})

        return {"status": "completed", "count": len(results), "results": results}

    return run_async(_find())


@celery_app.task(name="agents.lead_sourcing.upsert_lead", bind=True, max_retries=3)
def upsert_lead(self, contact_data: dict):
    """Upsert a lead from external source into DB"""
    async def _upsert():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
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
                details={"source": "lead_sourcing_agent", "contact_email": email},
            )
            db.add(audit)

            await db.commit()
            return {"lead_id": lead.id, "contact_id": contact.id}

    return run_async(_upsert())