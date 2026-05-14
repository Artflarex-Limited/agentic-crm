"""
AI Agents for Agentic CRM

Each agent is a Celery task that performs a specific role:
- lead_sourcing: Finds prospects on LinkedIn, web, forms
- email_outreach: Sends email sequences, handles bounces
- follow_up: Snooze management, auto-re-engage cold leads
- research: Enriches lead/company data from Apollo.io
- qualification: Scores and routes leads
- reporting: Daily summaries, pipeline alerts
"""
from app.agents.email_outreach import check_engagement, process_bounce, send_sequence
from app.agents.follow_up import process_cold_leads, schedule_follow_up, snooze_lead
from app.agents.lead_sourcing import find_leads_from_linkedin, upsert_lead
from app.agents.qualification import route_lead, score_lead
from app.agents.reporting import daily_summary, pipeline_alert, stalled_lead_warning
from app.agents.research import enrich_company, enrich_lead

__all__ = [
    "find_leads_from_linkedin",
    "upsert_lead",
    "send_sequence",
    "process_bounce",
    "check_engagement",
    "snooze_lead",
    "process_cold_leads",
    "schedule_follow_up",
    "enrich_lead",
    "enrich_company",
    "score_lead",
    "route_lead",
    "daily_summary",
    "pipeline_alert",
    "stalled_lead_warning",
]