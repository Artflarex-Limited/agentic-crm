"""
Tests for agent modules - standalone test file.
Run with: python -m pytest tests_standalone/test_agents_modules.py -v
"""
import json
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.modules['prisma'] = MagicMock()
sys.modules['prisma'].prisma = MagicMock()
sys.modules['prisma'].prisma.is_connected = True


@pytest.fixture
def mock_prisma():
    prisma_mock = MagicMock()
    prisma_mock.is_connected = True
    return prisma_mock


@pytest.fixture
def sample_lead():
    return MagicMock(id=1, score=50, stage="new")


@pytest.fixture
def sample_contact():
    return MagicMock(
        id=1,
        email="test@example.com",
        phone="+1-555-0100",
        linkedin_url="https://linkedin.com/in/test",
        title="Manager",
        company_id=1,
        extra_data=None
    )


class TestEmailOutreachAgent:
    """Tests for email_outreach agent functions."""

    @pytest.mark.asyncio
    async def test_send_sequence_enrollment_not_found(self, mock_prisma):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=None)
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_send_sequence_enrollment_inactive(self, mock_prisma, sample_lead):
        sample_lead.contact = MagicMock(email="test@example.com")
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="paused", currentStep=0, lead=sample_lead
        ))
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_send_sequence_completed(self, mock_prisma, sample_lead):
        sample_lead.contact = MagicMock(email="test@example.com")
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=100, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "email", "subject": "Test", "content": "Hello"}]
        ))
        mock_prisma.sequenceenrollment.update = AsyncMock()
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "completed"
        mock_prisma.sequenceenrollment.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sequence_no_contact_email(self, mock_prisma, sample_lead):
        sample_lead.contact = MagicMock(email=None)
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=0, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "email", "subject": "Test", "content": "Hello"}]
        ))
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "error"
        assert "no email" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_send_sequence_step_not_email(self, mock_prisma, sample_lead):
        sample_lead.contact = MagicMock(email="test@example.com")
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead_id=1, sequence_id=1, status="active", currentStep=0, lead=sample_lead
        ))
        mock_prisma.sequence.find_unique = AsyncMock(return_value=MagicMock(
            id=1, steps=[{"type": "task", "subject": "Test", "content": "Hello"}]
        ))
        mock_prisma.sequenceenrollment.update = AsyncMock()
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.send_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_process_bounce_not_found(self, mock_prisma):
        mock_prisma.activity.find_first = AsyncMock(return_value=None)
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
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
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.process_bounce("msg-123", "hard", {"reason": "test"})
        assert result["status"] == "processed"
        mock_prisma.lead.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_bounce_activity_without_lead(self, mock_prisma):
        mock_prisma.activity.find_first = AsyncMock(return_value=MagicMock(
            id=1, lead=None, activity_meta='{"message_id": "msg-123"}'
        ))
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.process_bounce("msg-123", "hard", {"reason": "test"})
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_check_engagement_no_activities(self, mock_prisma):
        sample_lead = MagicMock(id=1, score=50)
        mock_prisma.activity.find_many = AsyncMock(return_value=[])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.check_engagement(sample_lead.id)
        assert result["status"] == "no_engagement"

    @pytest.mark.asyncio
    async def test_check_engagement_with_replies(self, mock_prisma):
        sample_lead = MagicMock(id=1, score=50)
        mock_prisma.activity.find_many = AsyncMock(return_value=[
            MagicMock(type="email_replied"),
            MagicMock(type="email_opened"),
        ])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.check_engagement(sample_lead.id)
        assert result["status"] == "updated"
        assert result["score_delta"] == 20

    @pytest.mark.asyncio
    async def test_check_engagement_with_opens_only(self, mock_prisma):
        sample_lead = MagicMock(id=1, score=50)
        mock_prisma.activity.find_many = AsyncMock(return_value=[
            MagicMock(type="email_opened"),
        ])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.check_engagement(sample_lead.id)
        assert result["status"] == "updated"
        assert result["score_delta"] == 5

    @pytest.mark.asyncio
    async def test_check_engagement_lead_not_found(self, mock_prisma):
        mock_prisma.activity.find_many = AsyncMock(return_value=[])
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.check_engagement(1)
        assert result["status"] == "no_engagement"

    @pytest.mark.asyncio
    async def test_enroll_in_sequence_already_enrolled(self, mock_prisma):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=MagicMock(id=5))
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.enroll_in_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "already_enrolled"

    @pytest.mark.asyncio
    async def test_enroll_in_sequence_success(self, mock_prisma):
        mock_prisma.sequenceenrollment.find_first = AsyncMock(return_value=None)
        mock_prisma.sequenceenrollment.create = AsyncMock(return_value=MagicMock(id=10))
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import email_outreach
        email_outreach.prisma = mock_prisma
        result = await email_outreach.enroll_in_sequence(lead_id=1, sequence_id=1)
        assert result["status"] == "enrolled"
        assert result["enrollment_id"] == 10


class TestFollowUpAgent:
    """Tests for follow_up agent functions."""

    @pytest.mark.asyncio
    async def test_snooze_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import follow_up
        follow_up.prisma = mock_prisma
        result = await follow_up.snooze_lead(1, datetime.utcnow() + timedelta(days=1))
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_snooze_lead_success(self, mock_prisma):
        sample_lead = MagicMock(id=1)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        snooze_until = datetime.utcnow() + timedelta(days=3)
        from app.agents import follow_up
        follow_up.prisma = mock_prisma
        result = await follow_up.snooze_lead(sample_lead.id, snooze_until)
        assert result["status"] == "snoozed"
        mock_prisma.lead.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_cold_leads(self, mock_prisma):
        mock_lead = MagicMock(
            id=1, last_contacted_at=datetime.utcnow() - timedelta(days=10), stage="new"
        )
        mock_prisma.lead.find_many = AsyncMock(return_value=[mock_lead])
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import follow_up
        follow_up.prisma = mock_prisma
        result = await follow_up.process_cold_leads(days_threshold=7)
        assert result["status"] == "processed"
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_process_cold_leads_no_results(self, mock_prisma):
        mock_prisma.lead.find_many = AsyncMock(return_value=[])
        from app.agents import follow_up
        follow_up.prisma = mock_prisma
        result = await follow_up.process_cold_leads(days_threshold=7)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_schedule_follow_up_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import follow_up
        follow_up.prisma = mock_prisma
        result = await follow_up.schedule_follow_up(1, datetime.utcnow() + timedelta(days=1))
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_schedule_follow_up_success(self, mock_prisma):
        sample_lead = MagicMock(id=1)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        follow_up_date = datetime.utcnow() + timedelta(days=2)
        from app.agents import follow_up
        follow_up.prisma = mock_prisma
        result = await follow_up.schedule_follow_up(sample_lead.id, follow_up_date, "Test note")
        assert result["status"] == "scheduled"


class TestQualificationAgent:
    """Tests for qualification agent functions."""

    @pytest.mark.asyncio
    async def test_score_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import qualification
        qualification.prisma = mock_prisma
        result = await qualification.score_lead(1)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_score_lead_success(self, mock_prisma):
        sample_contact = MagicMock(
            email="test@example.com",
            phone="+1-555-0100",
            linkedin_url="https://linkedin.com/in/test",
            title="Manager",
            company_id=1
        )
        sample_lead = MagicMock(id=1, contact=sample_contact, stage="new", score=0)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import qualification
        qualification.prisma = mock_prisma
        result = await qualification.score_lead(sample_lead.id)
        assert result["status"] == "scored"
        assert result["score"] == 60
        assert result["stage"] == "contacted"

    @pytest.mark.asyncio
    async def test_score_lead_no_contact_fields(self, mock_prisma):
        sample_contact = MagicMock(
            email=None,
            phone=None,
            linkedin_url=None,
            title=None,
            company_id=None
        )
        sample_lead = MagicMock(id=1, contact=sample_contact, stage="new", score=0)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import qualification
        qualification.prisma = mock_prisma
        result = await qualification.score_lead(sample_lead.id)
        assert result["status"] == "scored"
        assert result["score"] == 0
        assert result["stage"] == "new"

    @pytest.mark.asyncio
    async def test_route_lead_to_outreach(self, mock_prisma):
        sample_lead = MagicMock(id=1, contact=MagicMock(spec=[]), score=55)
        sample_lead.assigned_agent_id = None
        sample_agent = MagicMock(id=1, spec=["id"])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.agent.find_first = AsyncMock(return_value=sample_agent)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock(return_value=MagicMock(id=1, spec=[]))
        from app.agents import qualification
        qualification.prisma = mock_prisma
        result = await qualification.route_lead(sample_lead.id)
        assert result["status"] == "routed"
        assert result["role"] == "outreach"
        assert result["agent_id"] == 1

    @pytest.mark.asyncio
    async def test_route_lead_to_research(self, mock_prisma):
        sample_lead = MagicMock(id=1, contact=MagicMock(spec=[]), score=30)
        sample_lead.assigned_agent_id = None
        sample_agent = MagicMock(id=2, spec=["id"])
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.agent.find_first = AsyncMock(return_value=sample_agent)
        mock_prisma.lead.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock(return_value=MagicMock(id=1, spec=[]))
        from app.agents import qualification
        qualification.prisma = mock_prisma
        result = await qualification.route_lead(sample_lead.id)
        assert result["status"] == "routed"
        assert result["role"] == "research"


class TestReportingAgent:
    """Tests for reporting agent functions."""

    @pytest.mark.asyncio
    async def test_daily_summary(self, mock_prisma):
        mock_prisma.lead.count = AsyncMock(return_value=5)
        mock_prisma.deal.count = AsyncMock(side_effect=[3, 10])
        mock_prisma.activity.find_many = AsyncMock(return_value=[])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import reporting
        reporting.prisma = mock_prisma
        result = await reporting.daily_summary()
        assert result["new_leads"] == 5
        assert result["new_deals"] == 3
        assert result["open_deals"] == 10

    @pytest.mark.asyncio
    async def test_pipeline_alert(self, mock_prisma):
        mock_deal = MagicMock(spec=["id", "name", "stage"])
        mock_deal.id = 1
        mock_deal.name = "Test Deal"
        mock_deal.stage = "qualified"
        mock_deal.updated_at = datetime.utcnow() - timedelta(days=15)
        mock_prisma.deal.find_many = AsyncMock(return_value=[mock_deal])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import reporting
        reporting.prisma = mock_prisma
        result = await reporting.pipeline_alert()
        assert result["status"] == "alert_generated"
        assert result["stalled_deals"] == 1

    @pytest.mark.asyncio
    async def test_pipeline_alert_no_stalled(self, mock_prisma):
        mock_prisma.deal.find_many = AsyncMock(return_value=[])
        from app.agents import reporting
        reporting.prisma = mock_prisma
        result = await reporting.pipeline_alert()
        assert result["stalled_deals"] == 0

    @pytest.mark.asyncio
    async def test_stalled_lead_warning(self, mock_prisma):
        mock_lead = MagicMock(
            id=1, score=10, stage="new",
            created_at=datetime.utcnow() - timedelta(days=20)
        )
        mock_prisma.lead.find_many = AsyncMock(return_value=[mock_lead])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import reporting
        reporting.prisma = mock_prisma
        result = await reporting.stalled_lead_warning(days_threshold=14)
        assert result["status"] == "warning_generated"
        assert result["stalled_leads"] == 1

    @pytest.mark.asyncio
    async def test_stalled_lead_warning_no_stalled(self, mock_prisma):
        mock_prisma.lead.find_many = AsyncMock(return_value=[])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import reporting
        reporting.prisma = mock_prisma
        result = await reporting.stalled_lead_warning(days_threshold=14)
        assert result["stalled_leads"] == 0


class TestResearchAgent:
    """Tests for research agent functions."""

    @pytest.mark.asyncio
    async def test_enrich_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import research
        research.prisma = mock_prisma
        result = await research.enrich_lead(1)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_enrich_lead_no_email(self, mock_prisma):
        sample_lead = MagicMock(id=1)
        sample_lead.contact = MagicMock(email=None)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        from app.agents import research
        research.prisma = mock_prisma
        result = await research.enrich_lead(sample_lead.id)
        assert result["status"] == "error"
        assert "no email" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_enrich_lead_success_with_company(self, mock_prisma):
        sample_contact = MagicMock(id=1, email="test@example.com", extra_data=None)
        sample_lead = MagicMock(id=1, contact=sample_contact)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        mock_prisma.company.find_first = AsyncMock(return_value=None)
        mock_prisma.company.create = AsyncMock(return_value=MagicMock(id=5))
        mock_prisma.contact.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import research
        research.prisma = mock_prisma
        mock_es = MagicMock()
        mock_es.enrich_contact = AsyncMock(return_value={
            "first_name": "John",
            "company_name": "Acme Corp"
        })
        research.enrichment_service = mock_es
        result = await research.enrich_lead(sample_lead.id)
        assert result["status"] == "enriched"

    @pytest.mark.asyncio
    async def test_enrich_lead_no_data(self, mock_prisma):
        sample_contact = MagicMock(id=1, email="test@example.com", extra_data=None)
        sample_lead = MagicMock(id=1, contact=sample_contact)
        mock_prisma.lead.find_unique = AsyncMock(return_value=sample_lead)
        from app.agents import research
        research.prisma = mock_prisma
        mock_es = MagicMock()
        mock_es.enrich_contact = AsyncMock(return_value={})
        research.enrichment_service = mock_es
        result = await research.enrich_lead(sample_lead.id)
        assert result["status"] == "no_data"

    @pytest.mark.asyncio
    async def test_enrich_company_not_found(self, mock_prisma):
        mock_prisma.company.find_unique = AsyncMock(return_value=None)
        from app.agents import research
        research.prisma = mock_prisma
        result = await research.enrich_company(1)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_enrich_company_success(self, mock_prisma):
        mock_company = MagicMock(id=1, name="Test Corp")
        mock_prisma.company.find_unique = AsyncMock(return_value=mock_company)
        mock_prisma.company.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import research
        research.prisma = mock_prisma
        mock_es = MagicMock()
        mock_es.enrich_company = AsyncMock(return_value={
            "industry": "Tech",
            "domain": "test.com"
        })
        research.enrichment_service = mock_es
        result = await research.enrich_company(1)
        assert result["status"] == "enriched"


class TestLeadSourcingAgent:
    """Tests for lead_sourcing agent functions."""

    @pytest.mark.asyncio
    async def test_find_leads_from_linkedin_no_results(self, mock_prisma):
        from app.agents import lead_sourcing
        lead_sourcing.prisma = mock_prisma
        mock_es_instance = MagicMock()
        mock_es_instance.search_contacts = AsyncMock(return_value=[])
        lead_sourcing.EnrichmentService = MagicMock(return_value=mock_es_instance)
        result = await lead_sourcing.find_leads_from_linkedin("engineer", limit=5)
        assert result["status"] == "completed"
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_find_leads_from_linkedin_success(self, mock_prisma):
        from app.agents import lead_sourcing
        lead_sourcing.prisma = mock_prisma
        mock_es_instance = MagicMock()
        mock_es_instance.search_contacts = AsyncMock(return_value=[
            {"email": "new@example.com", "first_name": "Jane", "company": {"name": "NewCo"}}
        ])
        lead_sourcing.EnrichmentService = MagicMock(return_value=mock_es_instance)
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
    async def test_upsert_lead_existing_contact(self, mock_prisma):
        sample_contact = MagicMock(id=10, email="existing@example.com")
        mock_prisma.contact.find_first = AsyncMock(return_value=sample_contact)
        mock_prisma.lead.create = AsyncMock(return_value=MagicMock(id=100))
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import lead_sourcing
        lead_sourcing.prisma = mock_prisma
        result = await lead_sourcing.upsert_lead({"email": "existing@example.com"})
        assert result["lead_id"] == 100


class TestSupplierMatchingAgent:
    """Tests for supplier_matching agent functions."""

    @pytest.mark.asyncio
    async def test_match_rfq_to_suppliers_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        result = await supplier_matching.match_rfq_to_suppliers(lead_id=1)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_match_rfq_to_suppliers_no_industry(self, mock_prisma):
        mock_lead = MagicMock(id=1, notes="", tags="[]")
        mock_prisma.lead.find_unique = AsyncMock(return_value=mock_lead)
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        result = await supplier_matching.match_rfq_to_suppliers(lead_id=1)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_match_rfq_to_suppliers_with_matches(self, mock_prisma):
        mock_lead = MagicMock(id=1, notes="manufacturing", tags='["cnc"]')
        mock_prisma.lead.find_unique = AsyncMock(return_value=mock_lead)
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        mock_sms = MagicMock()
        mock_sms.get_top_suppliers_for_rfq = AsyncMock(return_value=[
            MagicMock(
                supplier_id=1, company_name="Test Co", country="Turkey",
                match_score=0.85, match_reasons=["Made in Turkey"],
                certifications=["ISO9001"], production_capacity="1000/month",
                exporting_to_eu=True
            )
        ])
        mock_sms.record_match_event = AsyncMock()
        supplier_matching.supplier_matching_service = mock_sms
        result = await supplier_matching.match_rfq_to_suppliers(lead_id=1)
        assert result["status"] == "matched"
        assert result["match_count"] == 1

    @pytest.mark.asyncio
    async def test_score_supplier_matches_no_suppliers(self, mock_prisma):
        mock_prisma.supplier.find_many = AsyncMock(return_value=[])
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        result = await supplier_matching.score_supplier_matches([1, 2], "manufacturing")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_score_supplier_matches_success(self, mock_prisma):
        mock_supplier = MagicMock(
            id=1, companyName="Test Supplier", country="Turkey",
            industry="manufacturing", certifications='["ISO9001"]',
            productionCapacity="1000/month"
        )
        mock_prisma.supplier.find_many = AsyncMock(return_value=[mock_supplier])
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        mock_sms = MagicMock()
        mock_sms._calculate_match_score = MagicMock(return_value=(0.85, ["Made in Turkey"]))
        supplier_matching.supplier_matching_service = mock_sms
        result = await supplier_matching.score_supplier_matches([1], "manufacturing")
        assert result["status"] == "scored"
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_notify_suppliers(self, mock_prisma):
        mock_supplier = MagicMock(
            id=1, companyName="Test Supplier",
            businessEmail="test@supplier.com", status="VERIFIED"
        )
        mock_prisma.supplier.find_many = AsyncMock(return_value=[mock_supplier])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        result = await supplier_matching.notify_suppliers([1], "manufacturing", "Test RFQ")
        assert result["status"] == "notified"
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_verify_supplier_not_found(self, mock_prisma):
        mock_prisma.supplier.find_unique = AsyncMock(return_value=None)
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        result = await supplier_matching.verify_supplier(1)
        assert result["status"] == "error"


class TestRFQAgent:
    """Tests for rfq agent functions."""

    @pytest.mark.asyncio
    async def test_generate_rfq_from_qualified_leads(self, mock_prisma):
        mock_lead = MagicMock(id=1, contact_id=1, score=50, stage="contacted")
        mock_prisma.lead.find_many = AsyncMock(return_value=[mock_lead])
        mock_prisma.deal.find_first = AsyncMock(return_value=None)
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import rfq
        rfq.prisma = mock_prisma
        mock_rfq = MagicMock()
        mock_rfq.create_rfq_from_lead = AsyncMock(return_value={
            "deal_id": 10, "deal_value": 5000.0
        })
        rfq.get_rfq_service = AsyncMock(return_value=mock_rfq)
        result = await rfq.generate_rfq_from_qualified_leads(min_score=40)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_generate_rfq_from_qualified_leads_existing_deal(self, mock_prisma):
        mock_lead = MagicMock(id=1, contact_id=1, score=50, stage="contacted")
        mock_prisma.lead.find_many = AsyncMock(return_value=[mock_lead])
        mock_prisma.deal.find_first = AsyncMock(return_value=MagicMock(id=5))
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import rfq
        rfq.prisma = mock_prisma
        result = await rfq.generate_rfq_from_qualified_leads(min_score=40)
        assert result["status"] == "completed"
        assert result["generated_count"] == 0

    @pytest.mark.asyncio
    async def test_update_stale_rfqs(self, mock_prisma):
        mock_deal = MagicMock(id=1, name="Test", stage="lead")
        mock_prisma.deal.find_many = AsyncMock(return_value=[mock_deal])
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import rfq
        rfq.prisma = mock_prisma
        result = await rfq.update_stale_rfqs(days_threshold=7)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_stale_rfqs_no_stale(self, mock_prisma):
        mock_prisma.deal.find_many = AsyncMock(return_value=[])
        from app.agents import rfq
        rfq.prisma = mock_prisma
        result = await rfq.update_stale_rfqs(days_threshold=7)
        assert result["updated_count"] == 0

    @pytest.mark.asyncio
    async def test_check_expiring_rfqs(self, mock_prisma):
        future_date = datetime.utcnow() + timedelta(days=5)
        mock_deal = MagicMock(
            id=1, name="Test", value=1000.0,
            stage="lead", expectedCloseDate=future_date.isoformat()
        )
        mock_prisma.deal.find_many = AsyncMock(return_value=[mock_deal])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import rfq
        rfq.prisma = mock_prisma
        result = await rfq.check_expiring_rfqs(days_before=7)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_check_expiring_rfqs_no_expiring(self, mock_prisma):
        mock_prisma.deal.find_many = AsyncMock(return_value=[])
        from app.agents import rfq
        rfq.prisma = mock_prisma
        result = await rfq.check_expiring_rfqs(days_before=7)
        assert result["expiring_count"] == 0


class TestProcurementAgent:
    """Tests for procurement agent functions."""

    @pytest.mark.asyncio
    async def test_process_procurement_requests(self, mock_prisma):
        mock_req = MagicMock(id=1, status="SUBMITTED", extra_data=None, target_price=1000.0)
        mock_prisma.procurementrequest.find_many = AsyncMock(return_value=[mock_req])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import procurement
        procurement.prisma = mock_prisma
        mock_ps = MagicMock()
        mock_ms = MagicMock()
        mock_ms.get_top_suppliers_for_rfq = AsyncMock(return_value=[])
        mock_prisma.supplier.find_unique = AsyncMock(return_value=None)
        procurement.get_procurement_service = AsyncMock(return_value=mock_ps)
        procurement.get_supplier_matching_service = AsyncMock(return_value=mock_ms)
        result = await procurement.process_procurement_requests()
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_check_shipment_status(self, mock_prisma):
        mock_shipment = MagicMock(
            id=1, status="IN_TRANSIT",
            estimatedDeliveryDate=(datetime.utcnow() - timedelta(days=1)).isoformat(),
            trackingNumber="TRACK123"
        )
        mock_prisma.shipment.find_many = AsyncMock(return_value=[mock_shipment])
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import procurement
        procurement.prisma = mock_prisma
        result = await procurement.check_shipment_status()
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_check_shipment_status_no_alerts(self, mock_prisma):
        mock_prisma.shipment.find_many = AsyncMock(return_value=[])
        from app.agents import procurement
        procurement.prisma = mock_prisma
        result = await procurement.check_shipment_status()
        assert result["alert_count"] == 0

    @pytest.mark.asyncio
    async def test_process_supplier_payments(self, mock_prisma):
        mock_invoice = MagicMock(
            id=1, invoiceNumber="INV-001", status="SENT",
            purchaseOrderId=1, dueDate=(datetime.utcnow() - timedelta(days=10)).isoformat()
        )
        mock_prisma.invoice.find_many = AsyncMock(return_value=[mock_invoice])
        mock_prisma.invoice.update = AsyncMock()
        mock_prisma.activity.create = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import procurement
        procurement.prisma = mock_prisma
        result = await procurement.process_supplier_payments(days_overdue=7)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_auto_close_completed_orders(self, mock_prisma):
        mock_order = MagicMock(id=1, status="SHIPPED")
        mock_prisma.purchaseorder.find_many = AsyncMock(return_value=[mock_order])
        mock_prisma.shipment.find_many = AsyncMock(return_value=[
            MagicMock(status="DELIVERED")
        ])
        mock_prisma.invoice.find_many = AsyncMock(return_value=[
            MagicMock(status="PAID")
        ])
        mock_prisma.purchaseorder.update = AsyncMock()
        mock_prisma.auditlog.create = AsyncMock()
        from app.agents import procurement
        procurement.prisma = mock_prisma
        result = await procurement.auto_close_completed_orders()
        assert result["status"] == "completed"


class TestAgentContext:
    """Tests for agent context functions."""

    def test_generate_run_id(self):
        from app.agents.context import generate_run_id
        run_id = generate_run_id()
        assert len(run_id) == 16
        assert isinstance(run_id, str)

    def test_generate_correlation_id(self):
        from app.agents.context import generate_correlation_id
        corr_id = generate_correlation_id()
        assert corr_id.startswith("run-")
        assert isinstance(corr_id, str)

    def test_agent_context_initialization(self):
        from app.agents.context import AgentContext
        from app.models import AgentRole
        ctx = AgentContext(role=AgentRole.OUTREACH)
        assert ctx.run_id is not None
        assert ctx.correlation_id is not None
        assert ctx.role == AgentRole.OUTREACH

    def test_agent_context_to_dict(self):
        from app.agents.context import AgentContext
        from app.models import AgentRole
        ctx = AgentContext(role=AgentRole.RESEARCH)
        ctx_dict = ctx.to_dict()
        assert "run_id" in ctx_dict
        assert "correlation_id" in ctx_dict
        assert ctx_dict["role"] == AgentRole.RESEARCH.value