"""
Unit tests for Prisma models — CRUD operations
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.enums import ActivityType, AgentRole, AgentStatus, DealStage, LeadSource, LeadStage
from app.prisma import prisma


@pytest.mark.asyncio
async def test_company_crud(session_prisma):
    await prisma.company.delete_many(where={})
    created = await prisma.company.create(
        data={"name": "Test Co", "domain": "test.com", "industry": "Tech"}
    )
    assert created.id is not None
    assert created.name == "Test Co"
    assert created.createdAt is not None

    updated = await prisma.company.update(
        where={"id": created.id},
        data={"domain": "test.io"}
    )
    assert updated.domain == "test.io"

    deleted = await prisma.company.delete(where={"id": created.id})
    assert deleted is not None
    result = await prisma.company.find_unique(where={"id": created.id})
    assert result is None


@pytest.mark.asyncio
async def test_contact_crud(session_prisma, sample_company):
    contact = await prisma.contact.create(
        data={
            "companyId": sample_company.id,
            "firstName": "Alice",
            "lastName": "Smith",
            "email": "alice@test.com",
            "phone": "+1-555-1234",
            "title": "CEO"
        }
    )
    assert contact.id is not None
    assert contact.firstName == "Alice"
    fetched = await prisma.contact.find_unique(
        where={"id": contact.id},
        include={"company": True}
    )
    assert fetched.company.name == "Acme Corp"


@pytest.mark.asyncio
async def test_lead_crud(session_prisma, sample_contact):
    lead = await prisma.lead.create(
        data={
            "contactId": sample_contact.id,
            "source": LeadSource.LINKEDIN.value,
            "stage": LeadStage.NEW.value,
            "score": 75,
            "tags": "important,enterprise"
        }
    )
    assert lead.id is not None
    assert lead.score == 75
    assert lead.stage == LeadStage.NEW.value
    assert "important" in lead.tags


@pytest.mark.asyncio
async def test_lead_stage_transitions(session_prisma, sample_lead):
    for stage_value in [
        LeadStage.CONTACTED.value,
        LeadStage.QUALIFIED.value,
        LeadStage.PROPOSAL.value,
        LeadStage.NEGOTIATION.value,
    ]:
        updated = await prisma.lead.update(
            where={"id": sample_lead.id},
            data={"stage": stage_value}
        )
        assert updated.stage == stage_value


@pytest.mark.asyncio
async def test_lead_assignment_to_agent(session_prisma, sample_lead, sample_agent):
    updated = await prisma.lead.update(
        where={"id": sample_lead.id},
        data={"assignedAgentId": sample_agent.id}
    )
    assert updated.assignedAgentId == sample_agent.id

    fetched = await prisma.lead.find_unique(
        where={"id": sample_lead.id},
        include={"assignedAgent": True}
    )
    assert fetched.assignedAgent.name == "Outreach Agent"


@pytest.mark.asyncio
async def test_deal_crud(session_prisma, sample_contact, sample_company):
    deal = await prisma.deal.create(
        data={
            "contactId": sample_contact.id,
            "companyId": sample_company.id,
            "name": "Big Deal",
            "value": 100000.0,
            "stage": DealStage.LEAD.value,
            "expectedCloseDate": datetime.now(timezone.utc) + timedelta(days=60)
        }
    )
    assert deal.id is not None
    assert deal.value == 100000.0
    assert deal.stage == DealStage.LEAD.value


@pytest.mark.asyncio
async def test_deal_stage_transitions(session_prisma, sample_deal):
    for stage_value in [
        DealStage.QUALIFIED.value,
        DealStage.PROPOSAL.value,
        DealStage.NEGOTIATION.value,
        DealStage.WON.value,
    ]:
        updated = await prisma.deal.update(
            where={"id": sample_deal.id},
            data={"stage": stage_value}
        )
        assert updated.stage == stage_value


@pytest.mark.asyncio
async def test_agent_crud(session_prisma):
    agent = await prisma.agent.create(
        data={
            "name": "Research Agent",
            "role": AgentRole.RESEARCH.value,
            "status": AgentStatus.ACTIVE.value,
            "config": '{"max_calls": 20}',
            "description": "Company research agent"
        }
    )
    assert agent.id is not None
    assert agent.role == AgentRole.RESEARCH.value
    assert agent.status == AgentStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_agent_status_transitions(session_prisma, sample_agent):
    for status_value in [
        AgentStatus.PAUSED.value,
        AgentStatus.STOPPED.value,
        AgentStatus.ACTIVE.value,
    ]:
        updated = await prisma.agent.update(
            where={"id": sample_agent.id},
            data={"status": status_value}
        )
        assert updated.status == status_value


@pytest.mark.asyncio
async def test_sequence_crud(session_prisma):
    import json
    sequence = await prisma.sequence.create(
        data={
            "name": "Follow-up Sequence",
            "description": "Re-engagement emails",
            "steps": json.dumps([
                {"type": "email", "subject": "Checking in", "content": "Hi!", "delay_days": 1},
                {"type": "email", "subject": "Still interested?", "content": "Bump", "delay_days": 3},
            ]),
            "isActive": True
        }
    )
    assert sequence.id is not None
    steps = json.loads(sequence.steps) if sequence.steps else []
    assert len(steps) == 2
    assert sequence.isActive is True


@pytest.mark.asyncio
async def test_sequence_enrollment_crud(session_prisma, sample_lead, sample_sequence):
    enrollment = await prisma.sequenceenrollment.create(
        data={
            "leadId": sample_lead.id,
            "sequenceId": sample_sequence.id,
            "currentStep": 0,
            "status": "active"
        }
    )
    assert enrollment.id is not None
    assert enrollment.status == "active"

    fetched = await prisma.sequenceenrollment.find_unique(
        where={"id": enrollment.id},
        include={"lead": {"include": {"contact": True}}}
    )
    assert fetched.lead.contact.email == "john.doe@acme.com"


@pytest.mark.asyncio
async def test_activity_crud(session_prisma, sample_lead, sample_agent):
    activity = await prisma.activity.create(
        data={
            "leadId": sample_lead.id,
            "agentId": sample_agent.id,
            "type": ActivityType.EMAIL_SENT.value,
            "content": "Sent introductory email",
        }
    )
    assert activity.id is not None
    assert activity.type == ActivityType.EMAIL_SENT.value


@pytest.mark.asyncio
async def test_audit_log_crud(session_prisma, sample_agent):
    audit = await prisma.auditlog.create(
        data={
            "agentId": sample_agent.id,
            "action": "lead_stage_changed",
            "entityType": "lead",
            "entityId": 1,
            "details": '{"from": "new", "to": "contacted"}'
        }
    )
    assert audit.id is not None
    assert audit.action == "lead_stage_changed"

    fetched = await prisma.auditlog.find_unique(
        where={"id": audit.id},
        include={"agent": True}
    )
    assert fetched.agent.name == "Outreach Agent"


@pytest.mark.asyncio
async def test_company_relationships(session_prisma, sample_company, sample_contact, sample_deal):
    fetched = await prisma.company.find_unique(
        where={"id": sample_company.id},
        include={"contacts": True, "deals": True}
    )
    assert len(fetched.contacts) == 1
    assert fetched.contacts[0].email == "john.doe@acme.com"
    assert len(fetched.deals) == 1
    assert fetched.deals[0].name == "Acme Enterprise Deal"


@pytest.mark.asyncio
async def test_contact_relationships(session_prisma, sample_contact, sample_lead, sample_deal):
    fetched = await prisma.contact.find_unique(
        where={"id": sample_contact.id},
        include={"leads": True, "deals": True}
    )
    assert any(l.id == sample_lead.id for l in fetched.leads)
    assert any(d.id == sample_deal.id for d in fetched.deals)


@pytest.mark.asyncio
async def test_lead_snooze(session_prisma, sample_lead):
    future = datetime.now(timezone.utc) + timedelta(days=3)
    updated = await prisma.lead.update(
        where={"id": sample_lead.id},
        data={"snoozeUntil": future}
    )
    assert updated.snoozeUntil is not None
    assert abs((updated.snoozeUntil.replace(tzinfo=None) - future.replace(tzinfo=None)).total_seconds()) < 1


@pytest.mark.asyncio
async def test_lead_last_contacted(session_prisma, sample_lead):
    now = datetime.now(timezone.utc)
    updated = await prisma.lead.update(
        where={"id": sample_lead.id},
        data={"lastContactedAt": now}
    )
    assert updated.lastContactedAt is not None
    assert abs((updated.lastContactedAt.replace(tzinfo=None) - now.replace(tzinfo=None)).total_seconds()) < 1