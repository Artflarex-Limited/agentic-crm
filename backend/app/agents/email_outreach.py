"""
Email Outreach Agent
Sends email sequences, handles bounces, tracks opens/replies.
"""
import logging
import sys
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import (
    Activity,
    ActivityType,
    AgentRole,
    AuditLog,
    Lead,
    Sequence,
    SequenceEnrollment,
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
email_service = EmailService()


@celery_app.task(
    name="agents.email_outreach.send_sequence",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_sequence(self, lead_id: int, sequence_id: int, correlation_id: str | None = None):
    """
    Process next step in an email sequence for a lead.
    Sends email, logs activity, advances step.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Starting email sequence: lead_id={lead_id}, sequence_id={sequence_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _send_sequence():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
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
                logger.warning(
                    f"No enrollment found for lead {lead_id}, sequence {sequence_id}",
                    extra={"run_id": run_id}
                )
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
                logger.info(
                    f"Sequence completed for lead {lead_id}",
                    extra={"run_id": run_id, "lead_id": lead_id}
                )
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
                        "run_id": run_id,
                        "correlation_id": corr_id,
                        "message_id": f"seq-{sequence_id}-step-{current_step}-{lead_id}",
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
                        "run_id": run_id,
                        "correlation_id": corr_id,
                    },
                )
                db.add(audit)
                await db.commit()
                logger.info(
                    f"Email sent: lead_id={lead_id}, step={current_step}",
                    extra={"run_id": run_id, "lead_id": lead_id, "step": current_step}
                )
                return {"status": "sent", "lead_id": lead_id, "step": current_step}
            else:
                logger.warning(
                    f"Email send failed for lead {lead_id}, scheduling retry",
                    extra={"run_id": run_id, "lead_id": lead_id}
                )
                try:
                    raise Exception("Email send failed")
                except Exception:
                    self.retry(countdown=60, exc=sys.exc_info())

    return run_async(_send_sequence())


@celery_app.task(name="agents.email_outreach.process_bounce", bind=True, max_retries=3)
def process_bounce(self, message_id: str, bounce_type: str, details: dict, correlation_id: str | None = None):
    """
    Handle bounced email notification.
    Marks lead appropriately and logs the bounce.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Processing bounce: message_id={message_id}, type={bounce_type}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _process_bounce():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Activity)
                .where(Activity.activity_meta.op("->>")("message_id") == message_id)
                .options(selectinload(Activity.lead))
            )
            activity = result.scalar_one_or_none()
            if not activity or not activity.lead:
                logger.warning(
                    f"No activity found for bounce message_id={message_id}",
                    extra={"run_id": run_id}
                )
                return {"status": "ignored"}

            lead = activity.lead
            lead.notes = (lead.notes or "") + f"\n[Bounce {bounce_type}]: {details.get('reason', 'Unknown')}"

            audit = AuditLog(
                action="email_bounced",
                entity_type="lead",
                entity_id=lead.id,
                details={
                    "message_id": message_id,
                    "bounce_type": bounce_type,
                    "details": details,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()
            logger.info(
                f"Bounce processed: lead_id={lead.id}",
                extra={"run_id": run_id, "lead_id": lead.id}
            )
            return {"status": "processed", "lead_id": lead.id}

    return run_async(_process_bounce())


@celery_app.task(name="agents.email_outreach.check_engagement", bind=True, max_retries=3)
def check_engagement(self, lead_id: int, correlation_id: str | None = None):
    """
    Check if a lead has opened/replied to recent emails.
    Updates lead score based on engagement.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Checking engagement: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _check_engagement():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
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
                logger.info(
                    f"Engagement score updated: lead_id={lead_id}, delta={score_delta}",
                    extra={"run_id": run_id, "lead_id": lead_id, "score_delta": score_delta}
                )
                return {"status": "updated", "lead_id": lead_id, "score_delta": score_delta}

            return {"status": "error", "message": "Lead not found"}

    return run_async(_check_engagement())


@celery_app.task(name="agents.email_outreach.enroll_in_sequence", bind=True, max_retries=3)
def enroll_in_sequence(self, lead_id: int, sequence_id: int, correlation_id: str | None = None):
    """
    Enroll a lead in an email sequence.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Enrolling lead in sequence: lead_id={lead_id}, sequence_id={sequence_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _enroll():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            existing = await db.execute(
                select(SequenceEnrollment)
                .where(SequenceEnrollment.lead_id == lead_id)
                .where(SequenceEnrollment.sequence_id == sequence_id)
            )
            enrollment = existing.scalar_one_or_none()
            if enrollment:
                return {"status": "already_enrolled", "enrollment_id": enrollment.id}

            enrollment = SequenceEnrollment(
                lead_id=lead_id,
                sequence_id=sequence_id,
                current_step=0,
                status="active",
                enrolled_at=datetime.utcnow(),
            )
            db.add(enrollment)
            await db.flush()

            audit = AuditLog(
                action="sequence_enrolled",
                entity_type="lead",
                entity_id=lead_id,
                details={
                    "sequence_id": sequence_id,
                    "enrollment_id": enrollment.id,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()
            logger.info(
                f"Lead enrolled in sequence: lead_id={lead_id}, enrollment_id={enrollment.id}",
                extra={"run_id": run_id}
            )
            return {"status": "enrolled", "enrollment_id": enrollment.id}

    return run_async(_enroll())
