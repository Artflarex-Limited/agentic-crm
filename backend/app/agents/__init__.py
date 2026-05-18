"""
AI Agents for Agentic CRM

Each agent is a Celery task that performs a specific role:
- lead_sourcing: Finds prospects on LinkedIn, web, forms
- email_outreach: Sends email sequences, handles bounces
- follow_up: Snooze management, auto-re-engage cold leads
- research: Enriches lead/company data from Apollo.io
- qualification: Scores and routes leads
- reporting: Daily summaries, pipeline alerts

Context & Tracing:
All agents support correlation_id for distributed tracing and run_id
for individual execution tracking. Pass correlation_id through task
chains to enable end-to-end observability.
"""
from app.agents.context import AgentContext, AgentTaskMixin
from app.agents.email_outreach import (
    check_engagement,
    enroll_in_sequence,
    process_bounce,
    send_sequence,
)
from app.agents.follow_up import process_cold_leads, snooze_lead
from app.agents.lead_sourcing import find_leads_from_linkedin, upsert_lead
from app.agents.procurement import (
    auto_close_completed_orders,
    check_shipment_status,
    process_procurement_requests,
    process_supplier_payments,
)
from app.agents.qualification import route_lead, score_lead
from app.agents.reporting import daily_summary, pipeline_alert, stalled_lead_warning
from app.agents.research import enrich_company, enrich_lead
from app.agents.rfq import check_expiring_rfqs, generate_rfq_from_qualified_leads, update_stale_rfqs
from app.agents.supplier_matching import (
    match_rfq_to_suppliers,
    notify_suppliers,
    score_supplier_matches,
    verify_supplier,
)

__all__ = [
    "AgentContext",
    "AgentTaskMixin",
    "auto_close_completed_orders",
    "check_engagement",
    "check_expiring_rfqs",
    "check_shipment_status",
    "daily_summary",
    "enrich_company",
    "enrich_lead",
    "enroll_in_sequence",
    "find_leads_from_linkedin",
    "generate_rfq_from_qualified_leads",
    "match_rfq_to_suppliers",
    "notify_suppliers",
    "pipeline_alert",
    "process_bounce",
    "process_cold_leads",
    "process_procurement_requests",
    "process_supplier_payments",
    "route_lead",
    "score_lead",
    "score_supplier_matches",
    "send_sequence",
    "snooze_lead",
    "stalled_lead_warning",
    "upsert_lead",
    "update_stale_rfqs",
    "verify_supplier",
]
