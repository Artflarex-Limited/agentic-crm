"""
Lead Sourcing Agent
Finds and creates leads from LinkedIn, web forms, and cold outreach targets.
"""

from sqlalchemy import select

from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import AuditLog, Company, Contact, Lead, LeadSource


@celery_app.task(name="agents.lead_sourcing.find_from_linkedin")
def find_leads_from_linkedin(query: str, limit: int = 10):
    """
    Search Apollo.io for LinkedIn prospects matching query.
    Returns list of contact dicts that get upserted into the DB.
    """
    # TODO: Implement Apollo.io API call
    # from apollo_python_api import ApolloAPI
    # apollo = ApolloAPI(api_key=os.environ["APOLLO_API_KEY"])
    # results = apollo.search_contacts(query, limit=limit)
    pass


@celery_app.task(name="agents.lead_sourcing.upsert_lead")
async def upsert_lead(contact_data: dict):
    """Upsert a lead from external source into DB"""
    async with AsyncSessionLocal() as db:
        # Check if contact exists by email
        email = contact_data.get("email")
        if email:
            existing = await db.execute(
                select(Contact).where(Contact.email == email)
            )
            contact = existing.scalar_one_or_none()

        if not contact:
            # Create company if needed
            company_data = contact_data.pop("company", {})
            company = None
            if company_data.get("name"):
                company = Company(**company_data)
                db.add(company)
                await db.flush()

            # Create contact
            contact_data["company_id"] = company.id if company else None
            contact = Contact(**contact_data)
            db.add(contact)
            await db.flush()

        # Create lead
        lead = Lead(
            contact_id=contact.id,
            source=LeadSource.COLD_OUTREACH,
            score=contact_data.get("initial_score", 30),
        )
        db.add(lead)

        # Audit log
        audit = AuditLog(
            action="lead_created",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "lead_sourcing_agent", "contact_email": email},
        )
        db.add(audit)

        await db.commit()
        return {"lead_id": lead.id, "contact_id": contact.id}
