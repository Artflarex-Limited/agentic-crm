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
    async def test_process_bounce_not_found(self, mock_prisma):
        mock_prisma.activity.find_first = AsyncMock(return_value=None)
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
    async def test_route_lead_not_found(self, mock_prisma):
        mock_prisma.lead.find_unique = AsyncMock(return_value=None)
        from app.agents import qualification
        qualification.prisma = mock_prisma
        result = await qualification.route_lead(1)
        assert result["status"] == "error"


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
    async def test_pipeline_alert_no_stalled(self, mock_prisma):
        mock_prisma.deal.find_many = AsyncMock(return_value=[])
        from app.agents import reporting
        reporting.prisma = mock_prisma
        result = await reporting.pipeline_alert()
        assert result["stalled_deals"] == 0

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
    async def test_enrich_company_not_found(self, mock_prisma):
        mock_prisma.company.find_unique = AsyncMock(return_value=None)
        from app.agents import research
        research.prisma = mock_prisma
        result = await research.enrich_company(1)
        assert result["status"] == "error"


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
    async def test_score_supplier_matches_no_suppliers(self, mock_prisma):
        mock_prisma.supplier.find_many = AsyncMock(return_value=[])
        from app.agents import supplier_matching
        supplier_matching.prisma = mock_prisma
        result = await supplier_matching.score_supplier_matches([1, 2], "manufacturing")
        assert result["status"] == "error"

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
    async def test_update_stale_rfqs_no_stale(self, mock_prisma):
        mock_prisma.deal.find_many = AsyncMock(return_value=[])
        from app.agents import rfq
        rfq.prisma = mock_prisma
        result = await rfq.update_stale_rfqs(days_threshold=7)
        assert result["updated_count"] == 0

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