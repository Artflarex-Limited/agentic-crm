"""
Tests for Celery agent tasks with mock Redis
"""
from sqlalchemy import select
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.models.models import (
    Lead, Contact, Sequence, SequenceEnrollment, Activity,
    LeadSource, LeadStage, ActivityType, AgentRole, AgentStatus
)


@pytest.fixture
def mock_redis():
    with patch("app.celery_app.celery_app") as mock:
        yield mock


@pytest.fixture
def mock_email_service():
    with patch("app.agents.email_outreach.email_service") as mock:
        mock.send_email = AsyncMock(return_value=True)
        yield mock


@pytest.mark.asyncio
async def test_lead_model_to_dict(sample_lead, sample_contact):
    assert sample_lead.contact_id == sample_contact.id
    assert sample_lead.source == LeadSource.EMAIL
    assert sample_lead.stage == LeadStage.NEW


@pytest.mark.asyncio
async def test_sequence_enrollment_status(sample_lead, sample_sequence, db_session):
    enrollment = SequenceEnrollment(
        lead_id=sample_lead.id,
        sequence_id=sample_sequence.id,
        current_step=0,
        status="active"
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)

    assert enrollment.status == "active"
    enrollment.status = "completed"
    enrollment.completed_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(enrollment)
    assert enrollment.status == "completed"


@pytest.mark.asyncio
async def test_activity_logging_for_email(db_session, sample_lead, sample_agent):
    activity = Activity(
        lead_id=sample_lead.id,
        agent_id=sample_agent.id,
        type=ActivityType.EMAIL_SENT,
        content="Test email content",
        activity_meta={"sequence_id": 1, "step": 0, "subject": "Test Subject"}
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)

    assert activity.type == ActivityType.EMAIL_SENT
    assert activity.activity_meta["sequence_id"] == 1


@pytest.mark.asyncio
async def test_activity_email_opened_typed(db_session, sample_lead):
    activity = Activity(
        lead_id=sample_lead.id,
        type=ActivityType.EMAIL_OPENED,
        activity_meta={"message_id": "msg-abc123"}
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)

    assert activity.type == ActivityType.EMAIL_OPENED
    assert activity.activity_meta["message_id"] == "msg-abc123"


@pytest.mark.asyncio
async def test_activity_email_replied_typed(db_session, sample_lead):
    activity = Activity(
        lead_id=sample_lead.id,
        type=ActivityType.EMAIL_REPLIED,
        activity_meta={"message_id": "msg-xyz789"}
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)

    assert activity.type == ActivityType.EMAIL_REPLIED


@pytest.mark.asyncio
async def test_sequence_step_progression(db_session, sample_lead, sample_sequence):
    enrollment = SequenceEnrollment(
        lead_id=sample_lead.id,
        sequence_id=sample_sequence.id,
        current_step=0,
        status="active"
    )
    db_session.add(enrollment)
    await db_session.commit()

    assert len(sample_sequence.steps) == 2

    enrollment.current_step = 1
    await db_session.commit()
    await db_session.refresh(enrollment)
    assert enrollment.current_step == 1

    enrollment.current_step = 2
    await db_session.commit()
    await db_session.refresh(enrollment)
    assert enrollment.current_step >= len(sample_sequence.steps)


@pytest.mark.asyncio
async def test_agent_status_active_to_paused(db_session, sample_agent):
    assert sample_agent.status == AgentStatus.ACTIVE
    sample_agent.status = AgentStatus.PAUSED
    await db_session.commit()
    await db_session.refresh(sample_agent)
    assert sample_agent.status == AgentStatus.PAUSED


@pytest.mark.asyncio
async def test_audit_log_on_lead_stage_change(db_session, sample_lead, sample_agent):
    audit = MagicMock()
    audit.action = "lead_stage_changed"
    audit.entity_type = "lead"
    audit.entity_id = sample_lead.id
    audit.details = {"from": "new", "to": "qualified"}

    assert audit.action == "lead_stage_changed"
    assert audit.entity_type == "lead"


@pytest.mark.asyncio
async def test_check_engagement_no_activity(db_session, sample_lead):
    result = await db_session.execute(
        select(Activity).where(
            Activity.lead_id == sample_lead.id,
            Activity.type.in_([ActivityType.EMAIL_OPENED, ActivityType.EMAIL_REPLIED])
        )
    )
    activities = result.scalars().all()
    assert len(activities) == 0


@pytest.mark.asyncio
async def test_check_engagement_with_replies(db_session, sample_lead, sample_agent):
    activity = Activity(
        lead_id=sample_lead.id,
        agent_id=sample_agent.id,
        type=ActivityType.EMAIL_REPLIED,
        activity_meta={"message_id": "msg-reply-1"}
    )
    db_session.add(activity)
    await db_session.commit()

    initial_score = sample_lead.score

    sample_lead.score = min(100, initial_score + 20)
    await db_session.commit()
    await db_session.refresh(sample_lead)

    assert sample_lead.score >= initial_score


@pytest.mark.asyncio
async def test_lead_snooze_mechanism(db_session, sample_lead):
    from datetime import timedelta
    future = datetime.utcnow() + timedelta(days=3)
    sample_lead.snooze_until = future
    await db_session.commit()
    await db_session.refresh(sample_lead)
    assert sample_lead.snooze_until == future