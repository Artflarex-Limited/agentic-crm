"""
Email Outreach Agent
Sends email sequences, handles bounces, tracks opens/replies.

Refactored from Celery tasks to plain async functions using Prisma.
BackgroundTasks in the API layer calls these directly.
"""
import json
import logging
from datetime import datetime

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole
from app.prisma import prisma
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
email_service = EmailService()


async def send_sequence(lead_id: int, sequence_id: int, correlation_id: str | None = None):
    """
    Process next step in an email sequence for a lead.
    Sends email, logs activity, advances step.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Starting email sequence: lead_id={lead_id}, sequence_id={sequence_id}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    if not prisma.is_connected:
        logger.error("Database not configured", extra={"run_id": run_id})
        return {"status": "error", "message": "Database not configured"}

    # Fetch enrollment with lead + contact loaded
    enrollment = await prisma.sequenceenrollment.find_first(
        where={
            "lead_id": lead_id,
            "sequence_id": sequence_id,
        },
        include={
            "lead": {
                "include": {
                    "contact": True,
                }
            },
        },
    )
    if not enrollment:
        logger.warning(
            f"No enrollment found for lead {lead_id}, sequence {sequence_id}",
            extra={"run_id": run_id}
        )
        return {"status": "error", "message": "Enrollment not found"}

    if enrollment.status != "active":
        return {"status": "skipped", "reason": "Enrollment not active"}

    # Fetch sequence
    sequence = await prisma.sequence.find_unique(
        where={"id": sequence_id},
    )
    if not sequence or not sequence.steps:
        return {"status": "error", "message": "Sequence not found or empty"}

    steps = json.loads(sequence.steps) if isinstance(sequence.steps, str) else sequence.steps
    current_step = enrollment.currentStep

    if current_step >= len(steps):
        await prisma.sequenceenrollment.update(
            where={"id": enrollment.id},
            data={
                "status": "completed",
                "completedAt": datetime.utcnow(),
            },
        )
        logger.info(
            f"Sequence completed for lead {lead_id}",
            extra={"run_id": run_id, "lead_id": lead_id}
        )
        return {"status": "completed", "message": "All steps completed"}

    step = steps[current_step]
    if step.get("type") != "email":
        await prisma.sequenceenrollment.update(
            where={"id": enrollment.id},
            data={"currentStep": current_step + 1},
        )
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
        message_id = f"seq-{sequence_id}-step-{current_step}-{lead_id}"

        # Update enrollment
        await prisma.sequenceenrollment.update(
            where={"id": enrollment.id},
            data={
                "lastSentAt": datetime.utcnow(),
                "currentStep": current_step + 1,
            },
        )

        # Create activity
        await prisma.activity.create(
            data={
                "lead_id": lead_id,
                "contact_id": contact.id,
                "type": "email_sent",
                "content": (step.get("content", "") or "")[:500],
                "activityMeta": json.dumps({
                    "sequence_id": sequence_id,
                    "step": current_step,
                    "subject": step.get("subject"),
                    "run_id": run_id,
                    "correlation_id": corr_id,
                    "message_id": message_id,
                }),
            },
        )

        # Create audit log
        await prisma.auditlog.create(
            data={
                "action": "email_sent",
                "entityType": "lead",
                "entityId": lead_id,
                "details": json.dumps({
                    "contact_email": contact.email,
                    "sequence_id": sequence_id,
                    "step": current_step,
                    "run_id": run_id,
                    "correlation_id": corr_id,
                }),
            },
        )

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
        raise Exception("Email send failed")


async def process_bounce(message_id: str, bounce_type: str, details: dict, correlation_id: str | None = None):
    """
    Handle bounced email notification.
    Marks lead appropriately and logs the bounce.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Processing bounce: message_id={message_id}, type={bounce_type}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    if not prisma.is_connected:
        logger.error("Database not configured", extra={"run_id": run_id})
        return {"status": "error", "message": "Database not configured"}

    # Query activities where activity_meta->>'$.message_id' == message_id
    activity = await prisma.activity.find_first(
        where={
            "activity_meta": {
                "contains": f'"message_id": "{message_id}"',
            }
        },
        include={"lead": True},
    )

    if not activity or not activity.lead:
        logger.warning(
            f"No activity found for bounce message_id={message_id}",
            extra={"run_id": run_id}
        )
        return {"status": "ignored"}

    lead = activity.lead
    existing_notes = lead.notes or ""
    new_note = f"\n[Bounce {bounce_type}]: {details.get('reason', 'Unknown')}"

    await prisma.lead.update(
        where={"id": lead.id},
        data={"notes": existing_notes + new_note},
    )

    await prisma.auditlog.create(
        data={
            "action": "email_bounced",
            "entityType": "lead",
            "entityId": lead.id,
            "details": json.dumps({
                "message_id": message_id,
                "bounce_type": bounce_type,
                "details": details,
                "run_id": run_id,
                "correlation_id": corr_id,
            }),
        },
    )

    logger.info(
        f"Bounce processed: lead_id={lead.id}",
        extra={"run_id": run_id, "lead_id": lead.id}
    )
    return {"status": "processed", "lead_id": lead.id}


async def check_engagement(lead_id: int, correlation_id: str | None = None):
    """
    Check if a lead has opened/replied to recent emails.
    Updates lead score based on engagement.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Checking engagement: lead_id={lead_id}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    if not prisma.is_connected:
        logger.error("Database not configured", extra={"run_id": run_id})
        return {"status": "error", "message": "Database not configured"}

    activities = await prisma.activity.find_many(
        where={
            "lead_id": lead_id,
            "type": {"in": ["email_opened", "email_replied"]},
        },
        order={"createdAt": "desc"},
        take=5,
    )

    if not activities:
        return {"status": "no_engagement", "lead_id": lead_id}

    engaged_types = {a.type for a in activities}
    score_delta = 0
    if "email_replied" in engaged_types:
        score_delta = 20
    elif "email_opened" in engaged_types:
        score_delta = 5

    lead = await prisma.lead.find_unique(where={"id": lead_id})
    if lead:
        new_score = min(100, lead.score + score_delta)
        await prisma.lead.update(
            where={"id": lead_id},
            data={"score": new_score},
        )
        logger.info(
            f"Engagement score updated: lead_id={lead_id}, delta={score_delta}",
            extra={"run_id": run_id, "lead_id": lead_id, "score_delta": score_delta}
        )
        return {"status": "updated", "lead_id": lead_id, "score_delta": score_delta}

    return {"status": "error", "message": "Lead not found"}


async def enroll_in_sequence(lead_id: int, sequence_id: int, correlation_id: str | None = None):
    """
    Enroll a lead in an email sequence.
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Enrolling lead in sequence: lead_id={lead_id}, sequence_id={sequence_id}",
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    if not prisma.is_connected:
        logger.error("Database not configured", extra={"run_id": run_id})
        return {"status": "error", "message": "Database not configured"}

    existing = await prisma.sequenceenrollment.find_first(
        where={
            "lead_id": lead_id,
            "sequence_id": sequence_id,
        },
    )
    if existing:
        return {"status": "already_enrolled", "enrollment_id": existing.id}

    enrollment = await prisma.sequenceenrollment.create(
        data={
            "lead_id": lead_id,
            "sequence_id": sequence_id,
            "currentStep": 0,
            "status": "active",
            "enrolledAt": datetime.utcnow(),
        },
    )

    await prisma.auditlog.create(
        data={
            "action": "sequence_enrolled",
            "entityType": "lead",
            "entityId": lead_id,
            "details": json.dumps({
                "sequence_id": sequence_id,
                "enrollment_id": enrollment.id,
                "run_id": run_id,
                "correlation_id": corr_id,
            }),
        },
    )

    logger.info(
        f"Lead enrolled in sequence: lead_id={lead_id}, enrollment_id={enrollment.id}",
        extra={"run_id": run_id}
    )
    return {"status": "enrolled", "enrollment_id": enrollment.id}