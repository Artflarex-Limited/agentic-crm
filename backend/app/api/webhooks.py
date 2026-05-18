"""
Webhook endpoints for inbound lead ingestion.
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import validate_webhook_secret
from app.prisma import prisma

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

    name_parts = (payload.from_name or "").split(" ", 1)
    first_name = name_parts[0] if name_parts else None
    last_name = name_parts[1] if len(name_parts) > 1 else None

    contact = await prisma.contact.create(
        data={
            "email": payload.from_email,
            "firstName": first_name,
            "lastName": last_name,
        }
    )

    lead = await prisma.lead.create(
        data={
            "contactId": contact.id,
            "source": "email",
            "stage": "new",
            "score": 30,
            "utmSource": payload.utm_source,
            "utmMedium": payload.utm_medium,
            "utmCampaign": payload.utm_campaign,
            "utmTerm": payload.utm_term,
            "utmContent": payload.utm_content,
            "gaClientId": payload.ga_client_id,
        }
    )

    await prisma.auditlog.create(
        data={
            "action": "lead_created",
            "entityType": "lead",
            "entityId": lead.id,
            "details": json.dumps({"source": "inbound_email", "from_email": payload.from_email, "utm_source": payload.utm_source}),
        }
    )

    from app.services.ga4_service import generate_ga_client_id, get_ga4_service
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

    from app.services.hubspot_service import get_hubspot_service
    hubspot = await get_hubspot_service()
    await hubspot.sync_lead(
        lead_id=lead.id,
        email=payload.from_email,
        lead_data={
            "score": lead.score,
            "source": "email",
            "utm_source": payload.utm_source,
            "utm_medium": payload.utm_medium,
            "utm_campaign": payload.utm_campaign,
            "utm_term": payload.utm_term,
            "utm_content": payload.utm_content,
        },
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
    company_id = None
    if payload.company:
        company = await prisma.company.create(
            data={"name": payload.company}
        )
        company_id = company.id

    name_parts = payload.name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else None

    contact = await prisma.contact.create(
        data={
            "email": payload.email,
            "firstName": first_name,
            "lastName": last_name,
            "phone": payload.phone,
            "companyId": company_id,
        }
    )

    lead = await prisma.lead.create(
        data={
            "contactId": contact.id,
            "source": "web",
            "stage": "new",
            "score": 25,
            "notes": payload.message,
            "utmSource": payload.utm_source,
            "utmMedium": payload.utm_medium,
            "utmCampaign": payload.utm_campaign,
            "utmTerm": payload.utm_term,
            "utmContent": payload.utm_content,
            "gaClientId": payload.ga_client_id,
            "hubspotContactId": payload.hubspot_contact_id,
        }
    )

    await prisma.auditlog.create(
        data={
            "action": "lead_created",
            "entityType": "lead",
            "entityId": lead.id,
            "details": json.dumps({"source": "web_form", "email": payload.email, "utm_source": payload.utm_source, "utm_campaign": payload.utm_campaign}),
        }
    )

    from app.services.ga4_service import generate_ga_client_id, get_ga4_service
    ga4_service = await get_ga4_service()
    if payload.ga_client_id or payload.email:
        await ga4_service.track_form_submission(
            client_id=payload.ga_client_id or generate_ga_client_id(),
            form_name="web_form",
            lead_id=lead.id,
            user_email=payload.email,
        )

    from app.services.hubspot_service import get_hubspot_service
    hubspot = await get_hubspot_service()
    await hubspot.sync_lead(
        lead_id=lead.id,
        email=payload.email,
        lead_data={
            "score": lead.score,
            "source": "web",
            "utm_source": payload.utm_source,
            "utm_medium": payload.utm_medium,
            "utm_campaign": payload.utm_campaign,
            "utm_term": payload.utm_term,
            "utm_content": payload.utm_content,
        },
    )

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
    activities = await prisma.activity.find_many(
        where={
            "activityMeta": {
                "contains": f'"message_id": "{message_id}"'
            }
        },
        take=1,
    )
    activity = activities[0] if activities else None

    if activity:
        existing_meta = {}
        if activity.activityMeta:
            try:
                existing_meta = json.loads(activity.activityMeta)
            except (json.JSONDecodeError, TypeError):
                existing_meta = {}
        existing_meta["opened"] = True
        existing_meta["opened_at"] = datetime.utcnow().isoformat()
        await prisma.activity.update(
            where={"id": activity.id},
            data={"activityMeta": json.dumps(existing_meta)},
        )

    return {"status": "tracked"}


@router.post("/email/reply")
@limiter.limit(settings.rate_limit_webhooks)
async def email_reply(request: Request, message_id: str, recipient: str, body: str):
    """
    Track email replies.
    """
    activities = await prisma.activity.find_many(
        where={
            "activityMeta": {
                "contains": f'"message_id": "{message_id}"'
            }
        },
        take=1,
    )
    activity = activities[0] if activities else None

    if activity and activity.leadId:
        lead = await prisma.lead.find_first(where={"id": activity.leadId})
        if lead:
            await prisma.lead.update(
                where={"id": lead.id},
                data={"score": min(100, lead.score + 20)},
            )

        await prisma.activity.create(
            data={
                "leadId": activity.leadId,
                "contactId": activity.contactId,
                "type": "email_replied",
                "content": body[:500],
                "activityMeta": json.dumps({"original_message_id": message_id}),
            }
        )

    return {"status": "tracked"}
