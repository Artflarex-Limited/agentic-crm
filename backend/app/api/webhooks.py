"""
Webhook endpoints for inbound lead ingestion.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.models import Activity, AuditLog, Company, Contact, Lead, LeadSource

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


class InboundEmailPayload(BaseModel):
    from_email: EmailStr
    from_name: str | None = None
    subject: str
    body: str
    received_at: str | None = None


class WebFormPayload(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    company: str | None = None
    message: str | None = None
    source_url: str | None = None


class BouncePayload(BaseModel):
    message_id: str
    bounce_type: str
    reason: str | None = None
    details: dict | None = {}


@router.post("/inbound/email")
async def inbound_email(
    payload: InboundEmailPayload,
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
):
    """
    Receive inbound email leads.
    Creates contact and lead from email.
    """
    from app.core.config import get_settings
    settings = get_settings()

    if settings.outreach_requires_approval:
        webhook_secret = x_webhook_secret or ""
        expected = getattr(settings, "webhook_secret", "")
        if expected and webhook_secret != expected:
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
        )
        db.add(lead)

        audit = AuditLog(
            action="lead_created",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "inbound_email", "from_email": payload.from_email},
        )
        db.add(audit)
        await db.commit()

        logger.info(f"Inbound email lead created: {lead.id}")
        return {"status": "created", "lead_id": lead.id}


@router.post("/inbound/form")
async def inbound_form(payload: WebFormPayload):
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
        )
        db.add(lead)

        audit = AuditLog(
            action="lead_created",
            entity_type="lead",
            entity_id=lead.id,
            details={"source": "web_form", "email": payload.email},
        )
        db.add(audit)
        await db.commit()

        logger.info(f"Web form lead created: {lead.id}")
        return {"status": "created", "lead_id": lead.id}


@router.post("/email/bounce")
async def email_bounce(payload: BouncePayload):
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
async def email_open(message_id: str, recipient: str):
    """
    Track email opens (pixel or webhook from provider).
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Activity).where(Activity.metadata.op("->>")("message_id") == message_id)
        )
        activity = result.scalar_one_or_none()

        if activity:
            activity.metadata = {**activity.metadata, "opened": True, "opened_at": datetime.utcnow().isoformat()}
            await db.commit()

        return {"status": "tracked"}


@router.post("/email/reply")
async def email_reply(message_id: str, recipient: str, body: str):
    """
    Track email replies.
    """
    async with AsyncSessionLocal() as db:
        from app.models.models import ActivityType, Lead

        result = await db.execute(
            select(Activity).where(Activity.metadata.op("->>")("message_id") == message_id)
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
                metadata={"original_message_id": message_id},
            )
            db.add(reply_activity)
            await db.commit()

        return {"status": "tracked"}
