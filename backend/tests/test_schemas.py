"""
Pydantic schema validation tests
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.schemas.schemas import (
    CompanyCreate, CompanyResponse,
    ContactCreate, ContactResponse,
    LeadCreate, LeadUpdate, LeadResponse,
    DealCreate, DealUpdate, DealResponse,
    AgentCreate, AgentUpdate, AgentResponse,
    SequenceCreate, SequenceStep, SequenceResponse,
    ActivityCreate, ActivityResponse,
    DashboardStats, PipelineItem,
)
from app.models.models import LeadSource, LeadStage, DealStage, AgentRole, AgentStatus, ActivityType


def test_company_create_valid():
    company = CompanyCreate(name="Test Inc", domain="test.com", industry="SaaS")
    assert company.name == "Test Inc"
    assert company.domain == "test.com"


def test_company_create_minimal():
    company = CompanyCreate(name="Minimal Co")
    assert company.name == "Minimal Co"
    assert company.domain is None


def test_contact_create_valid():
    contact = ContactCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane@doe.com",
        phone="+1-555-0101"
    )
    assert contact.first_name == "Jane"
    assert contact.email == "jane@doe.com"


def test_contact_create_email_format(db_session):
    contact = ContactCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane@doe.com",
        phone="+1-555-0101"
    )
    assert contact.email == "jane@doe.com"


def test_lead_create_valid():
    lead = LeadCreate(
        contact_id=1,
        source=LeadSource.EMAIL,
        stage=LeadStage.NEW,
        score=50,
        tags=["warm", "enterprise"]
    )
    assert lead.contact_id == 1
    assert lead.score == 50


def test_lead_create_default_values():
    lead = LeadCreate(contact_id=1)
    assert lead.source == LeadSource.OTHER
    assert lead.stage == LeadStage.NEW
    assert lead.score == 0


def test_lead_update_partial():
    update = LeadUpdate(stage=LeadStage.QUALIFIED, score=80)
    data = update.model_dump(exclude_unset=True)
    assert data["stage"] == LeadStage.QUALIFIED
    assert data["score"] == 80


def test_lead_update_snooze():
    future = datetime.utcnow() + timedelta(days=5)
    update = LeadUpdate(snooze_until=future)
    assert update.snooze_until == future


def test_deal_create_valid():
    deal = DealCreate(
        contact_id=1,
        name="Enterprise Contract",
        value=150000.0,
        stage=DealStage.LEAD
    )
    assert deal.name == "Enterprise Contract"
    assert deal.value == 150000.0


def test_deal_create_default_stage():
    deal = DealCreate(contact_id=1, name="Small Deal")
    assert deal.stage == DealStage.LEAD
    assert deal.value == 0.0


def test_deal_update_partial():
    update = DealUpdate(stage=DealStage.NEGOTIATION)
    data = update.model_dump(exclude_unset=True)
    assert data["stage"] == DealStage.NEGOTIATION


def test_agent_create_valid():
    agent = AgentCreate(
        name="Outreach Bot",
        role=AgentRole.OUTREACH,
        status=AgentStatus.ACTIVE,
        config={"daily_limit": 100}
    )
    assert agent.role == AgentRole.OUTREACH
    assert agent.status == AgentStatus.ACTIVE


def test_agent_create_default_status():
    agent = AgentCreate(name="Research Bot", role=AgentRole.RESEARCH)
    assert agent.status == AgentStatus.PAUSED


def test_agent_update_partial():
    update = AgentUpdate(status=AgentStatus.PAUSED)
    data = update.model_dump(exclude_unset=True)
    assert data["status"] == AgentStatus.PAUSED


def test_sequence_step_valid():
    step = SequenceStep(type="email", subject="Hello", content="Hi there!", delay_days=2)
    assert step.type == "email"
    assert step.delay_days == 2


def test_sequence_create_valid():
    sequence = SequenceCreate(
        name="Welcome Campaign",
        description="Onboarding sequence",
        steps=[
            SequenceStep(type="email", subject="Welcome", content="Hello!", delay_days=0),
            SequenceStep(type="email", subject="Follow up", content="How are you?", delay_days=3),
        ],
        is_active=True
    )
    assert len(sequence.steps) == 2
    assert sequence.is_active is True


def test_sequence_create_empty_steps():
    sequence = SequenceCreate(name="Empty Sequence", steps=[])
    assert sequence.steps == []


def test_activity_create_valid():
    activity = ActivityCreate(
        lead_id=1,
        agent_id=1,
        type=ActivityType.EMAIL_SENT,
        content="Sent test email",
        metadata={"message_id": "msg-123"}
    )
    assert activity.type == ActivityType.EMAIL_SENT
    assert activity.metadata["message_id"] == "msg-123"


def test_activity_create_minimal():
    activity = ActivityCreate(type=ActivityType.NOTE_ADDED, content="Called and left voicemail")
    assert activity.type == ActivityType.NOTE_ADDED


def test_dashboard_stats_valid():
    stats = DashboardStats(
        total_leads=42,
        total_contacts=30,
        total_deals=15,
        open_deals_value=500000.0,
        leads_by_stage={"new": 10, "qualified": 15},
        deals_by_stage={"lead": 5, "qualified": 7},
        recent_activities=[]
    )
    assert stats.total_leads == 42
    assert stats.open_deals_value == 500000.0


def test_pipeline_item_valid():
    item = PipelineItem(
        id=1,
        name="Big Deal",
        contact_name="John Doe",
        company_name="Acme Corp",
        value=75000.0,
        stage=DealStage.QUALIFIED,
        expected_close_date=datetime.utcnow() + timedelta(days=30)
    )
    assert item.name == "Big Deal"
    assert item.stage == DealStage.QUALIFIED


def test_lead_stage_enum_values():
    assert LeadStage.NEW.value == "new"
    assert LeadStage.QUALIFIED.value == "qualified"
    assert LeadStage.WON.value == "won"
    assert LeadStage.LOST.value == "lost"


def test_deal_stage_enum_values():
    assert DealStage.LEAD.value == "lead"
    assert DealStage.PROPOSAL.value == "proposal"
    assert DealStage.NEGOTIATION.value == "negotiation"
    assert DealStage.WON.value == "won"


def test_agent_role_enum_values():
    assert AgentRole.OUTREACH.value == "outreach"
    assert AgentRole.RESEARCH.value == "research"
    assert AgentRole.LEAD_SOURCING.value == "lead_sourcing"


def test_activity_type_enum_values():
    assert ActivityType.EMAIL_SENT.value == "email_sent"
    assert ActivityType.EMAIL_OPENED.value == "email_opened"
    assert ActivityType.EMAIL_REPLIED.value == "email_replied"
    assert ActivityType.CALL_MADE.value == "call_made"