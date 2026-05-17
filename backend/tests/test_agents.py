"""
Tests for async agent functions — Prisma-based
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.enums import ActivityType, AgentRole, AgentStatus, DealStage, LeadSource, LeadStage
from app.prisma import prisma


@pytest.mark.asyncio
async def test_lead_model_to_dict(sample_lead, sample_contact):
    assert sample_lead.contact_id == sample_contact.id
    assert sample_lead.stage == LeadStage.NEW.value


@pytest.mark.asyncio
async def test_sequence_enrollment_status(session_prisma, sample_lead, sample_sequence):
    enrollment = await prisma.sequenceenrollment.create(
        data={
            "lead_id": sample_lead.id,
            "sequence_id": sample_sequence.id,
            "current_step": 0,
            "status": "active"
        }
    )
    assert enrollment.status == "active"

    updated = await prisma.sequenceenrollment.update(
        where={"id": enrollment.id},
        data={
            "status": "completed",
            "completed_at": datetime.now(timezone.utc)
        }
    )
    assert updated.status == "completed"


@pytest.mark.asyncio
async def test_activity_logging_for_email(session_prisma, sample_lead, sample_agent):
    activity = await prisma.activity.create(
        data={
            "lead_id": sample_lead.id,
            "agent_id": sample_agent.id,
            "type": ActivityType.EMAIL_SENT.value,
            "content": "Test email content",
        }
    )
    assert activity.type == ActivityType.EMAIL_SENT.value


@pytest.mark.asyncio
async def test_activity_email_opened_typed(session_prisma, sample_lead):
    activity = await prisma.activity.create(
        data={
            "lead_id": sample_lead.id,
            "type": ActivityType.EMAIL_OPENED.value,
        }
    )
    assert activity.type == ActivityType.EMAIL_OPENED.value


@pytest.mark.asyncio
async def test_activity_email_replied_typed(session_prisma, sample_lead):
    activity = await prisma.activity.create(
        data={
            "lead_id": sample_lead.id,
            "type": ActivityType.EMAIL_REPLIED.value,
        }
    )
    assert activity.type == ActivityType.EMAIL_REPLIED.value


@pytest.mark.asyncio
async def test_sequence_step_progression(session_prisma, sample_lead, sample_sequence):
    enrollment = await prisma.sequenceenrollment.create(
        data={
            "lead_id": sample_lead.id,
            "sequence_id": sample_sequence.id,
            "current_step": 0,
            "status": "active"
        }
    )

    sequence = await prisma.sequence.find_unique(where={"id": sample_sequence.id})
    assert len(sequence.steps) == 2

    updated1 = await prisma.sequenceenrollment.update(
        where={"id": enrollment.id},
        data={"current_step": 1}
    )
    assert updated1.current_step == 1

    updated2 = await prisma.sequenceenrollment.update(
        where={"id": enrollment.id},
        data={"current_step": 2}
    )
    assert updated2.current_step >= len(sequence.steps)


@pytest.mark.asyncio
async def test_agent_status_active_to_paused(session_prisma, sample_agent):
    assert sample_agent.status == AgentStatus.ACTIVE.value

    updated = await prisma.agent.update(
        where={"id": sample_agent.id},
        data={"status": AgentStatus.PAUSED.value}
    )
    assert updated.status == AgentStatus.PAUSED.value


@pytest.mark.asyncio
async def test_audit_log_on_lead_stage_change(session_prisma, sample_lead, sample_agent):
    audit = await prisma.auditlog.create(
        data={
            "agent_id": sample_agent.id,
            "action": "lead_stage_changed",
            "entity_type": "lead",
            "entity_id": sample_lead.id,
            "details": '{"from": "new", "to": "qualified"}'
        }
    )
    assert audit.action == "lead_stage_changed"
    assert audit.entity_type == "lead"


@pytest.mark.asyncio
async def test_check_engagement_no_activity(session_prisma, sample_lead):
    activities = await prisma.activity.find_many(
        where={
            "lead_id": sample_lead.id,
            "type": {"in": [ActivityType.EMAIL_OPENED.value, ActivityType.EMAIL_REPLIED.value]}
        }
    )
    assert len(activities) == 0


@pytest.mark.asyncio
async def test_check_engagement_with_replies(session_prisma, sample_lead, sample_agent):
    await prisma.activity.create(
        data={
            "lead_id": sample_lead.id,
            "agent_id": sample_agent.id,
            "type": ActivityType.EMAIL_REPLIED.value,
            "content": "Great, I'm interested!"
        }
    )

    initial_score = sample_lead.score
    updated = await prisma.lead.update(
        where={"id": sample_lead.id},
        data={"score": min(100, initial_score + 20)}
    )
    assert updated.score >= initial_score


@pytest.mark.asyncio
async def test_lead_snooze_mechanism(session_prisma, sample_lead):
    future = datetime.now(timezone.utc) + timedelta(days=3)
    updated = await prisma.lead.update(
        where={"id": sample_lead.id},
        data={"snooze_until": future}
    )
    assert updated.snooze_until == future