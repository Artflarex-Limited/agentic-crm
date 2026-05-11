"""
Email Outreach Agent
Sends email sequences, handles bounces, tracks opens/replies.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import (
    Activity,
    ActivityType,
    AuditLog,
    Lead,
    Sequence,
    SequenceEnrollment,
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
email_service = EmailService()


@celery_app.task(name="agents.email_outreach.send_sequence")
def send_sequence(lead_id: int, sequence_id: int):
    """
    Process next step in an email sequence for a lead.
    Sends email, logs activity, advances step.
    """

    async def _send_sequence():
        async with AsyncSessionLocal() as db:
            enrollment = await db.execute(
                select(SequenceEnrollment)
                .where(SequenceEnrollment.lead_id == lead_id)
                .where(SequenceEnrollment.sequence_id == sequence_id)
                .options(selectinload(SequenceEnrollment.lead).selectinload(Lead.contact))
            )
            enrollment = enrollment.scalar_one_or_none()
            if not enrollment:
                logger.warning(f"No enrollment found for lead {lead_id}, sequence {sequence_id}")
                return {"status": "error", "message": "Enrollment not found"}

            if enrollment.status != "active":
                return {"status": "skipped", "reason": "Enrollment not active"}

            sequence = await db.execute(
                select(Sequence).where(Sequence.id == sequence_id)
            )
            sequence = sequence.scalar_one_or_none()
            if not sequence or not sequence.steps:
                return {"status": "error", "message": "Sequence not found or empty"}

            current_step = enrollment.current_step
            if current_step >= len(sequence.steps):
                enrollment.status = "completed"
                enrollment.completed_at = datetime.utcnow()
                await db.commit()
                return {"status": "completed", "message": "All steps completed"}

            step = sequence.steps[current_step]
            if step.get("type") != "email":
                enrollment.current_step = current_step + 1
                await db.commit()
                return {"status": "skipped", "reason": "Step is not email type"}

            lead = enrollment.lead
            contact = lead.contact
            if not contact or not contact.email:
                return {"status": "error", "message": "Contact has no email"}

            sent = await email_service.send_email(
                to_email=contact.email,
                subject=step.get("subject", f"Follow-up from {lead.id}"),
                body=step.get("content", ""),
            )

            if sent:
                enrollment.last_sent_at = datetime.utcnow()
                enrollment.current_step = current_step + 1

                activity = Activity(
                    lead_id=lead_id,
                    contact_id=contact.id,
                    type=ActivityType.EMAIL_SENT,
                    content=step.get("content", "")[:500],
                    metadata={
                        "sequence_id": sequence_id,
                        "step": current_step,
                        "subject": step.get("subject"),
                    },
                )
                db.add(activity)

                audit = AuditLog(
                    action="email_sent",
                    entity_type="lead",
                    entity_id=lead_id,
                    details={
                        "contact_email": contact.email,
                        "sequence_id": sequence_id,
                        "step": current_step,
                    },
                )
                db.add(audit)
                await db.commit()
                return {"status": "sent", "lead_id": lead_id, "step": current_step}
            else:
                return {"status": "error", "message": "Failed to send email"}

    return _run_async(_send_sequence())


@celery_app.task(name="agents.email_outreach.process_bounce")
def process_bounce(message_id: str, bounce_type: str, details: dict):
    """
    Handle bounced email notification.
    Marks lead appropriately and logs the bounce.
    """
    async def _process_bounce():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Activity)
                .where(Activity.metadata.op("->>")("message_id") == message_id)
                .options(selectinload(Activity.lead))
            )
            activity = result.scalar_one_or_none()
            if not activity or not activity.lead:
                logger.warning(f"No activity found for bounce message_id={message_id}")
                return {"status": "ignored"}

            lead = activity.lead
            lead.notes = (lead.notes or "") + f"\n[Bounce {bounce_type}]: {details.get('reason', 'Unknown')}"

            audit = AuditLog(
                action="email_bounced",
                entity_type="lead",
                entity_id=lead.id,
                details={"message_id": message_id, "bounce_type": bounce_type, "details": details},
            )
            db.add(audit)
            await db.commit()
            return {"status": "processed", "lead_id": lead.id}

    return _run_async(_process_bounce())


@celery_app.task(name="agents.email_outreach.check_engagement")
def check_engagement(lead_id: int):
    """
    Check if a lead has opened/replied to recent emails.
    Updates lead score based on engagement.
    """
    async def _check_engagement():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Activity)
                .where(Activity.lead_id == lead_id)
                .where(Activity.type.in_([ActivityType.EMAIL_OPENED, ActivityType.EMAIL_REPLIED]))
                .order_by(Activity.created_at.desc())
                .limit(5)
            )
            activities = result.scalars().all()

            if not activities:
                return {"status": "no_engagement", "lead_id": lead_id}

            engaged_types = {a.type for a in activities}
            score_delta = 0
            if ActivityType.EMAIL_REPLIED in engaged_types:
                score_delta = 20
            elif ActivityType.EMAIL_OPENED in engaged_types:
                score_delta = 5

            lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = lead_result.scalar_one_or_none()
            if lead:
                lead.score = min(100, lead.score + score_delta)
                await db.commit()
                return {"status": "updated", "lead_id": lead_id, "score_delta": score_delta}

            return {"status": "error", "message": "Lead not found"}

    return _run_async(_check_engagement())


def _run_async(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)
