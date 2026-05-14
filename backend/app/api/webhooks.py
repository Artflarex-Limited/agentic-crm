"""
Webhook endpoints for inbound lead ingestion.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.core.rate_limit import limiter
from app.core.security import validate_webhook_secret
from app.db.database import AsyncSessionLocal
from app.models.models import Activity, AuditLog, Company, Contact, Lead, LeadSource

from app.core.config import get_settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)
settings = get_settings()


class InboundEmailPayload(BaseModel):
    from_email: EmailStr
    from_name: str | None = None
    subject: str
    body: str
    received_at: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    ga_client_id: str | None = None


class WebFormPayload(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    company: str | None = None
    message: str | None = None
    source_url: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    ga_client_id: str | None = None
    hubspot_contact_id: str | None = None


class BouncePayload(BaseModel):
    message_id: str
    bounce_type: str
    reason: str | None = None
    details: dict | None = {}


@router.post("/inbound/email")
@limiter.limit(settings.rate_limit_webhooks)
async def inbound_email(
    request: Request,
    payload: InboundEmailPayload,
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
):
    """
    Receive inbound email leads.
    Creates contact and lead from email.
    """
    if not validate_webhook_secret(x_webhook_secret or "", settings.webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    async with AsyncSessionLocal() as db:
        name_parts = (payload.from_name or "").split(" ", 1)
        first_name = name_parts[0] if name_parts else None
        last_name = name_parts[1] if len(name_parts) > 1 else None

        contact = Contact(
            email=payload.from_email,
            first_name=first_name,
            last_name=last_name,
        )
        db.add(contact)
        await db.flush()

        lead = Lead(
            contact_id=contact.id,
            source=LeadSource.EMAIL,
            score=30,
            utm_source=payload.utm_source,
            utm_medium=payload.utm_medium,
            utm_campaign=payload.utm_campaign,
            utm_term=payload.utm_term,
            utm_content=payload.utm_content,
            ga_client_id=payload.ga_client_id,
        )
        db.add(lead)

        audit = AuditLog(
            action="lead_created",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "inbound_email", "from_email": payload.from_email, "utm_source": payload.utm_source},
        )
        db.add(audit)
        await db.commit()

        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        if payload.ga_client_id or payload.from_email:
            await ga4_service.track_lead_created(
                client_id=payload.ga_client_id or generate_ga_client_id(),
                lead_id=lead.id,
                source="email",
                utm_source=payload.utm_source,
                utm_campaign=payload.utm_campaign,
                user_email=payload.from_email,
            )

        logger.info(f"Inbound email lead created: {lead.id}")
        return {"status": "created", "lead_id": lead.id}


@router.post("/inbound/form")
@limiter.limit(settings.rate_limit_webhooks)
async def inbound_form(request: Request, payload: WebFormPayload):
    """
    Receive web form submissions.
    Creates contact and lead.
    """
    async with AsyncSessionLocal() as db:
        company = None
        if payload.company:
            company = Company(name=payload.company)
            db.add(company)
            await db.flush()

        name_parts = payload.name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else None

        contact = Contact(
            email=payload.email,
            first_name=first_name,
            last_name=last_name,
            phone=payload.phone,
            company_id=company.id if company else None,
        )
        db.add(contact)
        await db.flush()

        lead = Lead(
            contact_id=contact.id,
            source=LeadSource.WEB,
            score=25,
            notes=payload.message,
            utm_source=payload.utm_source,
            utm_medium=payload.utm_medium,
            utm_campaign=payload.utm_campaign,
            utm_term=payload.utm_term,
            utm_content=payload.utm_content,
            ga_client_id=payload.ga_client_id,
            hubspot_contact_id=payload.hubspot_contact_id,
        )
        db.add(lead)

        audit = AuditLog(
            action="lead_created",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "web_form", "email": payload.email, "utm_source": payload.utm_source, "utm_campaign": payload.utm_campaign},
        )
        db.add(audit)

        from app.services.ga4_service import get_ga4_service, generate_ga_client_id
        ga4_service = await get_ga4_service()
        if payload.ga_client_id or payload.email:
            await ga4_service.track_form_submission(
                client_id=payload.ga_client_id or generate_ga_client_id(),
                form_name="web_form",
                lead_id=lead.id,
                user_email=payload.email,
            )
        await db.commit()

        logger.info(f"Web form lead created: {lead.id}")
        return {"status": "created", "lead_id": lead.id}


@router.post("/email/bounce")
@limiter.limit(settings.rate_limit_webhooks)
async def email_bounce(request: Request, payload: BouncePayload):
    """
    Receive bounce notifications from email provider.
    """
    from app.agents.email_outreach import process_bounce

    result = process_bounce(
        message_id=payload.message_id,
        bounce_type=payload.bounce_type,
        details=payload.details or {},
    )

    logger.info(f"Bounce processed: {result}")
    return result


@router.post("/email/open")
@limiter.limit(settings.rate_limit_webhooks)
async def email_open(request: Request, message_id: str, recipient: str):
    """
    Track email opens (pixel or webhook from provider).
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Activity).where(Activity.metadata.op("->>")("message_id") == message_id)
        )
        activity = result.scalar_one_or_none()

        if activity:
            activity.activity_meta = {**activity.activity_meta, "opened": True, "opened_at": datetime.utcnow().isoformat()}
            await db.commit()

        return {"status": "tracked"}


@router.post("/email/reply")
@limiter.limit(settings.rate_limit_webhooks)
async def email_reply(request: Request, message_id: str, recipient: str, body: str):
    """
    Track email replies.
    """
    async with AsyncSessionLocal() as db:
        from app.models.models import ActivityType, Lead

        result = await db.execute(
            select(Activity).where(Activity.activity_meta.op("->>")("message_id") == message_id)
        )
        activity = result.scalar_one_or_none()

        if activity and activity.lead_id:
            lead_result = await db.execute(select(Lead).where(Lead.id == activity.lead_id))
            lead = lead_result.scalar_one_or_none()
            if lead:
                lead.score = min(100, lead.score + 20)

            reply_activity = Activity(
                lead_id=activity.lead_id,
                contact_id=activity.contact_id,
                type=ActivityType.EMAIL_REPLIED,
                content=body[:500],
                activity_meta={"original_message_id": message_id},
            )
            db.add(reply_activity)
            await db.commit()

        return {"status": "tracked"}
