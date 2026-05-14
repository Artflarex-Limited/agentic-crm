"""
Email Outreach Agent
Sends email sequences, handles bounces, tracks opens/replies.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import (
    Activity,
    ActivityType,
    AuditLog,
    Lead,
    Sequence,
    SequenceEnrollment,
)
from app.services.email_service import EmailService
from app.agents._async import run_async

logger = logging.getLogger(__name__)
email_service = EmailService()


@celery_app.task(name="agents.email_outreach.send_sequence", bind=True, max_retries=3)
def send_sequence(self, lead_id: int, sequence_id: int):
    """
    Process next step in an email sequence for a lead.
    Sends email, logs activity, advances step.
    """

    async def _send_sequence():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
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
                    activity_meta={
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
                try:
                    self.retry(countdown=60, exc=Exception("Email send failed"))
                except Exception:
                    return {"status": "error", "message": "Failed to send email"}

    return run_async(_send_sequence())


@celery_app.task(name="agents.email_outreach.process_bounce", bind=True, max_retries=3)
def process_bounce(self, message_id: str, bounce_type: str, details: dict):
    """
    Handle bounced email notification.
    Marks lead appropriately and logs the bounce.
    """
    async def _process_bounce():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Activity)
                .where(Activity.activity_meta.op("->>")("message_id") == message_id)
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

    return run_async(_process_bounce())


@celery_app.task(name="agents.email_outreach.check_engagement", bind=True, max_retries=3)
def check_engagement(self, lead_id: int):
    """
    Check if a lead has opened/replied to recent emails.
    Updates lead score based on engagement.
    """
    async def _check_engagement():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured")
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
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

    return run_async(_check_engagement())