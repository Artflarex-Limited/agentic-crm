"""
Tests for agent modules to improve coverage.
Covers: email_outreach, follow_up, research, qualification, reporting,
lead_sourcing, supplier_matching, rfq, procurement agents.
"""
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.agents import (
    email_outreach,
    follow_up,
    qualification,
    reporting,
    research,
    lead_sourcing,
)
from app.agents.context import AgentContext, generate_run_id, generate_correlation_id
from app.models.models import AgentRole, LeadStage, DealStage


@pytest.fixture
def mock_prisma():
    with patch("app.prisma.prisma") as mock:
        mock.is_connected = True
        yield mock


@pytest.fixture
def mock_email_service():
    with patch("app.agents.email_outreach.email_service") as mock:
        mock.send_email = AsyncMock(return_value=True)
        yield mock


class TestEmailOutreach:
    """Tests for email_outreach agent functions."""

    @pytest.mark.asyncio
    async def test_send_sequence_enrollment_not_found(self, mock_prisma):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=None)

        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_send_sequence_enrollment_inactive(self, mock_prisma, sample_lead, sample_sequence):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="paused", currentStep=0, lead=sample_lead
        ))

        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_send_sequence_completed(self, mock_prisma, sample_lead, sample_sequence):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=100, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "email", "subject": "Test", "content": "Hello"}]
        ))
        mock_prisma.sequenceenrollment.update = AsyncMock()

        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "completed"
        mock_prisma.sequenceenrollment.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sequence_no_contact_email(self, mock_prisma, sample_lead, sample_sequence):
        sample_lead.contact = MagicMock(email=None)
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=0, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "email", "subject": "Test", "content": "Hello"}]
        ))

        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "error"
        assert "no email" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_send_sequence_success(self, mock_prisma, mock_email_service, sample_lead, sample_sequence):
        sample_contact = MagicMock(id=1, email="test@example.com")
        sample_lead.contact = sample_contact

        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=0, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "email", "subject": "Test", "content": "Hello"}]
        ))
        mock_prisma.sequenceenrollment.update = AsyncMock()
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "sent"
        assert result["step"] == 0
        mock_email_service.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sequence_email_failed(self, mock_prisma, sample_lead, sample_sequence):
        sample_contact = MagicMock(id=1, email="test@example.com")
        sample_lead.contact = sample_contact

        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=0, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "email", "subject": "Test", "content": "Hello"}]
        ))
        mock_email_service.send_email = AsyncMock(return_value=False)

        with pytest.raises(Exception, match="Email send failed"):
            await email_outreach.send_sequence(lead_id=1, sequence_id=1)

    @pytest.mark.asyncio
    async def test_process_bounce_not_found(self, mock_prisma):
        mock_prisma.activity.find_first = AsyncMock(return_value=None)

        result = await email_outreach.process_bounce("msg-123", "hard", {"reason": "test"})

        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_process_bounce_success(self, mock_prisma):
        mock_lead = MagicMock(id=1, notes="")
        mock_prisma.activity.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead=mock_lead, activity_meta='{"message_id": "msg-123"}'
        ))
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        result = await email_outreach.process_bounce("msg-123", "hard", {"reason": "test"})

        assert result["status"] == "processed"
        mock_prisma.lead.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_engagement_no_activities(self, mock_prisma, sample_lead):
        mock_prisma.activity.find_many = AsyncMock(return_value=[])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)

        result = await email_outreach.check_engagement(sample_lead.id)

        assert result["status"] == "no_engagement"

    @pytest.mark.asyncio
    async def test_check_engagement_with_replies(self, mock_prisma, sample_lead):
        sample_lead.score = 50
        mock_prisma.activity.find_many = AsyncMock(return_value=[
            MagicMock(type="email_replied"),
            MagicMock(type="email_opened"),
        ])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()

        result = await email_outreach.check_engagement(sample_lead.id)

        assert result["status"] == "updated"
        assert result["score_delta"] == 20

    @pytest.mark.asyncio
    async def test_enroll_in_sequence_already_enrolled(self, mock_prisma):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(id=5))

        result = await email_outreach.enroll_in_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "already_enrolled"

    @pytest.mark.asyncio
    async def test_enroll_in_sequence_success(self, mock_prisma):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=None)
        mock_prisma.sequenceenrollment.create = AsyncMock(return_value=MagicMock(id=10))
        mock_prisma.auditlog.create = AsyncMock()

        result = await email_outreach.enroll_in_sequence(lead_id=1, sequence_id=1)

        assert result["status"] == "enrolled"
        assert result["enrollment_id"] == 10


class TestFollowUp:
    """Tests for follow_up agent functions."""

    @pytest.mark.asyncio
    async def test_snooze_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)

        result = await follow_up.snooze_lead(1, datetime.utcnow() + timedelta(days=1))

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_snooze_lead_success(self, mock_prisma, sample_lead):
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        snooze_until = datetime.utcnow() + timedelta(days=3)
        result = await follow_up.snooze_lead(sample_lead.id, snooze_until)

        assert result["status"] == "snoozed"
        mock_prisma.lead.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_cold_leads(self, mock_prisma):
        mock_lead = MagicMock(
            id=1, last_contacted_at=datetime.utcnow() - timedelta(days=10), stage="NEW"
        )
        mock_prisma.lead.find_many = AsyncMock(return_value=[mock_lead])
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        result = await follow_up.process_cold_leads(days_threshold=7)

        assert result["status"] == "processed"
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_schedule_follow_up_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)

        result = await follow_up.schedule_follow_up(1, datetime.utcnow() + timedelta(days=1))

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_schedule_follow_up_success(self, mock_prisma, sample_lead):
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        follow_up_date = datetime.utcnow() + timedelta(days=2)
        result = await follow_up.schedule_follow_up(sample_lead.id, follow_up_date, "Test note")

        assert result["status"] == "scheduled"


class TestQualification:
    """Tests for qualification agent functions."""

    @pytest.mark.asyncio
    async def test_score_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)

        result = await qualification.score_lead(1)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_score_lead_success(self, mock_prisma, sample_lead, sample_contact):
        sample_lead.contact = sample_contact
        sample_contact.email = "test@example.com"
        sample_contact.phone = "+1-555-0100"
        sample_contact.linkedin_url = "https://linkedin.com/in/test"
        sample_contact.title = "Manager"
        sample_contact.company_id = 1

        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        result = await qualification.score_lead(sample_lead.id)

        assert result["status"] == "scored"
        assert result["score"] == 60
        assert result["stage"] == LeadStage.CONTACTED.value

    @pytest.mark.asyncio
    async def test_route_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)

        result = await qualification.route_lead(1)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_route_lead_success(self, mock_prisma, sample_lead, sample_agent):
        sample_lead.contact = MagicMock()
        sample_lead.score = 55

        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.agent.find_first = AsyncMock(return_value=sample_agent)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        result = await qualification.route_lead(sample_lead.id)

        assert result["status"] == "routed"
        assert result["role"] == AgentRole.OUTREACH.value


class TestReporting:
    """Tests for reporting agent functions."""

    @pytest.mark.asyncio
    async def test_daily_summary(self, mock_prisma):
        mock_prisma.lead.count = AsyncMock(return_value=5)
        mock_prisma.deal.count = AsyncMock(side_effect=[3, 10])
        mock_prisma.activity.find_many = AsyncMock(return_value=[])
        mock_prisma.auditlog.create = AsyncMock()

        result = await reporting.daily_summary()

        assert result["new_leads"] == 5
        assert result["new_deals"] == 3
        assert result["open_deals"] == 10

    @pytest.mark.asyncio
    async def test_pipeline_alert(self, mock_prisma):
        mock_deal = MagicMock(
            id=1, name="Test Deal", stage=DealStage.LEAD.value,
            updated_at=datetime.utcnow() - timedelta(days=15)
        )
        mock_prisma.deal.find_many = AsyncMock(return_value=[mock_deal])
        mock_prisma.auditlog.create = AsyncMock()

        result = await reporting.pipeline_alert()

        assert result["status"] == "alert_generated"
        assert result["stalled_deals"] == 1

    @pytest.mark.asyncio
    async def test_stalled_lead_warning(self, mock_prisma):
        mock_lead = MagicMock(
            id=1, score=10, stage=LeadStage.NEW.value,
            created_at=datetime.utcnow() - timedelta(days=20)
        )
        mock_prisma.lead.find_many = AsyncMock(return_value=[mock_lead])
        mock_prisma.auditlog.create = AsyncMock()

        result = await reporting.stalled_lead_warning(days_threshold=14)

        assert result["status"] == "warning_generated"
        assert result["stalled_leads"] == 1


class TestResearch:
    """Tests for research agent functions."""

    @pytest.mark.asyncio
    async def test_enrich_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)

        result = await research.enrich_lead(1)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_enrich_lead_no_email(self, mock_prisma, sample_lead):
        sample_lead.contact = MagicMock(email=None)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)

        result = await research.enrich_lead(sample_lead.id)

        assert result["status"] == "error"
        assert "no email" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_enrich_lead_success(self, mock_prisma, sample_lead, sample_contact):
        sample_contact.email = "test@example.com"
        sample_lead.contact = sample_contact

        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.company.find_first = AsyncMock(return_value=None)
        mock_prisma.company.create = AsyncMock(return_value=MagicMock(id=5))
        mock_prisma.contact.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        with patch("app.agents.research.enrichment_service") as mock_es:
            mock_es.enrich_contact = AsyncMock(return_value={
                "first_name": "John",
                "company_name": "Acme Corp"
            })

            result = await research.enrich_lead(sample_lead.id)

            assert result["status"] == "enriched"

    @pytest.mark.asyncio
    async def test_enrich_company_not_found(self, mock_prisma):
        mock_prisma.company.find_unique = AsyncMock(return_value=None)

        result = await research.enrich_company(1)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_enrich_company_success(self, mock_prisma):
        mock_company = MagicMock(id=1, name="Test Corp")
        mock_prisma.company.find_unique = AsyncMock(return_value=mock_company)
        mock_prisma.company.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()

        with patch("app.agents.research.enrichment_service") as mock_es:
            mock_es.enrich_company = AsyncMock(return_value={
                "industry": "Tech",
                "domain": "test.com"
            })

            result = await research.enrich_company(1)

            assert result["status"] == "enriched"


class TestLeadSourcing:
    """Tests for lead_sourcing agent functions."""

    @pytest.mark.asyncio
    async def test_find_leads_from_linkedin_no_results(self, mock_prisma):
        with patch("app.agents.lead_sourcing.EnrichmentService") as mock_es:
            mock_es.return_value.search_contacts = AsyncMock(return_value=[])

            result = await lead_sourcing.find_leads_from_linkedin("engineer", limit=5)

            assert result["status"] == "completed"
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_find_leads_from_linkedin_success(self, mock_prisma, sample_contact):
        with patch("app.agents.lead_sourcing.EnrichmentService") as mock_es:
            mock_es.return_value.search_contacts = AsyncMock(return_value=[
                {"email": "new@example.com", "first_name": "Jane", "company": {"name": "NewCo"}}
            ])

            mock_prisma.contact.find_first = AsyncMock(return_value=None)
            mock_prisma.company.find_first = AsyncMock(return_value=None)
            mock_prisma.company.create = AsyncMock(return_value=MagicMock(id=2))
            mock_prisma.contact.create = AsyncMock(return_value=MagicMock(id=10))
            mock_prisma.lead.create = AsyncMock(return_value=MagicMock(id=100))
            mock_prisma.auditlog.create = AsyncMock()

            result = await lead_sourcing.find_leads_from_linkedin("engineer", limit=5)

            assert result["status"] == "completed"
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_upsert_lead_existing_contact(self, mock_prisma, sample_contact):
        mock_prisma.contact.find_first = AsyncMock(return_value=sample_contact)
        mock_prisma.lead.create = AsyncMock(return_value=MagicMock(id=100))
        mock_prisma.auditlog.create = AsyncMock()

        result = await lead_sourcing.upsert_lead({"email": "existing@example.com"})

        assert result["lead_id"] == 100


class TestAgentContext:
    """Tests for agent context functions."""

    def test_generate_run_id(self):
        run_id = generate_run_id()
        assert len(run_id) == 16
        assert isinstance(run_id, str)

    def test_generate_correlation_id(self):
        corr_id = generate_correlation_id()
        assert corr_id.startswith("run-")
        assert isinstance(corr_id, str)

    def test_agent_context_set_and_get(self):
        ctx = AgentContext(role=AgentRole.OUTREACH)
        assert ctx.run_id is not None
        assert ctx.correlation_id is not None
        assert ctx.role == AgentRole.OUTREACH

    def test_agent_context_to_dict(self):
        ctx = AgentContext(role=AgentRole.RESEARCH)
        ctx_dict = ctx.to_dict()
        assert "run_id" in ctx_dict
        assert "correlation_id" in ctx_dict
        assert ctx_dict["role"] == AgentRole.RESEARCH.value