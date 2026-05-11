"""
Unit tests for SQLAlchemy models — CRUD operations
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import selectinload

from app.models.models import (
    Activity,
    ActivityType,
    Agent,
    AgentRole,
    AgentStatus,
    AuditLog,
    Company,
    Contact,
    Deal,
    DealStage,
    Lead,
    LeadSource,
    LeadStage,
    Sequence,
    SequenceEnrollment,
)


@pytest.mark.asyncio
async def test_company_crud(db_session):
    company = Company(name="Test Co", domain="test.com", industry="Tech")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    assert company.id is not None
    assert company.name == "Test Co"
    assert company.created_at is not None

    company.domain = "test.io"
    await db_session.commit()
    await db_session.refresh(company)
    assert company.domain == "test.io"

    await db_session.delete(company)
    await db_session.commit()
    result = await db_session.get(Company, company.id)
    assert result is None


@pytest.mark.asyncio
async def test_contact_crud(db_session, sample_company):
    contact = Contact(
        company_id=sample_company.id,
        first_name="Alice",
        last_name="Smith",
        email="alice@test.com",
        phone="+1-555-1234",
        title="CEO"
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    assert contact.id is not None
    assert contact.first_name == "Alice"
    assert contact.company.name == "Acme Corp"


@pytest.mark.asyncio
async def test_lead_crud(db_session, sample_contact):
    lead = Lead(
        contact_id=sample_contact.id,
        source=LeadSource.LINKEDIN,
        stage=LeadStage.NEW,
        score=75,
        tags=["important", "enterprise"]
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    assert lead.id is not None
    assert lead.score == 75
    assert LeadStage.NEW in [lead.stage]
    assert "important" in lead.tags


@pytest.mark.asyncio
async def test_lead_stage_transitions(db_session, sample_lead):
    stages = [LeadStage.CONTACTED, LeadStage.QUALIFIED, LeadStage.PROPOSAL, LeadStage.NEGOTIATION]
    for stage in stages:
        sample_lead.stage = stage
        await db_session.commit()
        await db_session.refresh(sample_lead)
        assert sample_lead.stage == stage


@pytest.mark.asyncio
async def test_lead_assignment_to_agent(db_session, sample_lead, sample_agent):
    sample_lead.assigned_agent_id = sample_agent.id
    await db_session.commit()
    await db_session.refresh(sample_lead)

    assert sample_lead.assigned_agent_id == sample_agent.id
    assert sample_lead.assigned_agent.name == "Outreach Agent"


@pytest.mark.asyncio
async def test_deal_crud(db_session, sample_contact, sample_company):
    deal = Deal(
        contact_id=sample_contact.id,
        company_id=sample_company.id,
        name="Big Deal",
        value=100000.0,
        stage=DealStage.LEAD,
        expected_close_date=datetime.utcnow() + timedelta(days=60)
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)

    assert deal.id is not None
    assert deal.value == 100000.0
    assert deal.stage == DealStage.LEAD


@pytest.mark.asyncio
async def test_deal_stage_transitions(db_session, sample_deal):
    for stage in [DealStage.QUALIFIED, DealStage.PROPOSAL, DealStage.NEGOTIATION, DealStage.WON]:
        sample_deal.stage = stage
        await db_session.commit()
        await db_session.refresh(sample_deal)
        assert sample_deal.stage == stage


@pytest.mark.asyncio
async def test_agent_crud(db_session):
    agent = Agent(
        name="Research Agent",
        role=AgentRole.RESEARCH,
        status=AgentStatus.ACTIVE,
        config={"max_calls": 20},
        description="Company research agent"
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    assert agent.id is not None
    assert agent.role == AgentRole.RESEARCH
    assert agent.status == AgentStatus.ACTIVE


@pytest.mark.asyncio
async def test_agent_status_transitions(db_session, sample_agent):
    for status in [AgentStatus.PAUSED, AgentStatus.STOPPED, AgentStatus.ACTIVE]:
        sample_agent.status = status
        await db_session.commit()
        await db_session.refresh(sample_agent)
        assert sample_agent.status == status


@pytest.mark.asyncio
async def test_sequence_crud(db_session):
    sequence = Sequence(
        name="Follow-up Sequence",
        description="Re-engagement emails",
        steps=[
            {"type": "email", "subject": "Checking in", "content": "Hi!", "delay_days": 1},
            {"type": "email", "subject": "Still interested?", "content": "Bump", "delay_days": 3},
        ],
        is_active=True
    )
    db_session.add(sequence)
    await db_session.commit()
    await db_session.refresh(sequence)

    assert sequence.id is not None
    assert len(sequence.steps) == 2
    assert sequence.is_active is True


@pytest.mark.asyncio
async def test_sequence_enrollment_crud(db_session, sample_lead, sample_sequence):
    enrollment = SequenceEnrollment(
        lead_id=sample_lead.id,
        sequence_id=sample_sequence.id,
        current_step=0,
        status="active"
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)

    assert enrollment.id is not None
    assert enrollment.status == "active"
    assert enrollment.lead.contact.email == "john.doe@acme.com"


@pytest.mark.asyncio
async def test_activity_crud(db_session, sample_lead, sample_agent):
    activity = Activity(
        lead_id=sample_lead.id,
        agent_id=sample_agent.id,
        type=ActivityType.EMAIL_SENT,
        content="Sent introductory email",
        activity_meta={"subject": "Hello"}
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)

    assert activity.id is not None
    assert activity.type == ActivityType.EMAIL_SENT
    assert activity.activity_meta["subject"] == "Hello"


@pytest.mark.asyncio
async def test_audit_log_crud(db_session, sample_agent):
    audit = AuditLog(
        agent_id=sample_agent.id,
        action="lead_stage_changed",
        entity_type="lead",
        entity_id=1,
        details={"from": "new", "to": "contacted"}
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.id is not None
    assert audit.action == "lead_stage_changed"
    assert audit.agent.name == "Outreach Agent"


@pytest.mark.asyncio
async def test_company_relationships(db_session, sample_company, sample_contact, sample_deal):
    from sqlalchemy import select
    result = await db_session.execute(
        select(Company).where(Company.id == sample_company.id).options(
selectinload(Company.contacts),
        selectinload(Company.deals)
        )
    )
    company = result.scalar_one()
    assert len(company.contacts) == 1
    assert company.contacts[0].email == "john.doe@acme.com"
    assert len(company.deals) == 1
    assert company.deals[0].name == "Acme Enterprise Deal"


@pytest.mark.asyncio
async def test_contact_relationships(db_session, sample_contact, sample_lead, sample_deal):
    from sqlalchemy import select
    result = await db_session.execute(
        select(Contact).where(Contact.id == sample_contact.id).options(
            selectinload(Contact.leads),
            selectinload(Contact.deals)
        )
    )
    contact = result.scalar_one()
    assert sample_lead in contact.leads
    assert sample_deal in contact.deals


@pytest.mark.asyncio
async def test_lead_snooze(db_session, sample_lead):
    future_date = datetime.utcnow() + timedelta(days=3)
    sample_lead.snooze_until = future_date
    await db_session.commit()
    await db_session.refresh(sample_lead)

    assert sample_lead.snooze_until == future_date


@pytest.mark.asyncio
async def test_lead_last_contacted(db_session, sample_lead):
    now = datetime.utcnow()
    sample_lead.last_contacted_at = now
    await db_session.commit()
    await db_session.refresh(sample_lead)

    assert sample_lead.last_contacted_at == now
