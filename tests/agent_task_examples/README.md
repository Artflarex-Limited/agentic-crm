# Agent Task Examples

This directory contains task definitions that QA can run against the Agentic CRM system to verify agent functionality.

## Task Categories

### Lead Sourcing Tasks

#### TASK-LS-001: Source leads from LinkedIn
- **Agent**: Lead Sourcing Agent
- **Description**: Find 10 companies in the SaaS industry with 100-500 employees and create lead entries for key contacts
- **Expected Outcome**: 10 new lead records created with source="linkedin", contact info populated
- **Validation**: Check `/api/leads/` returns 10 new leads, each with contact.email and contact.company populated

#### TASK-LS-002: Enrich lead data via Apollo.io
- **Agent**: Research Agent
- **Description**: Enrich existing leads with company data (domain, industry, LinkedIn URL)
- **Expected Outcome**: Lead records updated with enriched company information
- **Validation**: Check that enriched leads have non-null company.domain and company.industry

### Outreach Tasks

#### TASK-OR-001: Send welcome email sequence
- **Agent**: Outreach Agent
- **Description**: Enroll new leads in the "Welcome Sequence" and trigger first step
- **Expected Outcome**: SequenceEnrollment created, first email sent, Activity logged
- **Validation**: Check `/api/activities/` for email_sent activity, check lead score updated

#### TASK-OR-002: Handle email bounce
- **Agent**: Outreach Agent
- **Description**: Process bounce notification for a previously sent email
- **Expected Outcome**: Lead notes updated with bounce info, AuditLog entry created
- **Validation**: Check lead.notes contains "[Bounce" string

### Follow-up Tasks

#### TASK-FU-001: Re-engage cold leads
- **Agent**: Follow-up Agent
- **Description**: Find leads with last_contacted_at > 7 days ago and stage="contacted", send follow-up
- **Expected Outcome**: New activity created, lead stage transitions
- **Validation**: Check for follow-up activities on cold leads

#### TASK-FU-002: Snooze lead for 3 days
- **Agent**: Follow-up Agent
- **Description**: Snooze a lead that requested follow-up in 3 days
- **Expected Outcome**: lead.snooze_until = now + 3 days
- **Validation**: Check lead.snooze_until is set to future date

### Qualification Tasks

#### TASK-QL-001: Score and route leads
- **Agent**: Qualification Agent
- **Description**: Score all NEW leads and route to appropriate agents based on score
- **Expected Outcome**: Lead scores calculated (0-100), leads assigned to agents based on score thresholds
- **Validation**: Check leads have score 0-100, high-score leads have assigned_agent_id

#### TASK-QL-002: Advance qualified leads to proposal stage
- **Agent**: Qualification Agent
- **Description**: Identify leads with score > 70 and advance to PROPOSAL stage
- **Expected Outcome**: Lead stage changed to "proposal", activity logged
- **Validation**: Check lead.stage = "proposal" for qualified leads

### Reporting Tasks

#### TASK-RP-001: Generate daily pipeline report
- **Agent**: Reporting Agent
- **Description**: Generate report of pipeline status (deals by stage, total value, stalled deals)
- **Expected Outcome**: Report with deals_by_stage, open_deals_value, stalled deal warnings
- **Validation**: Dashboard stats API returns accurate counts

#### TASK-RP-002: Alert on stalled deals
- **Agent**: Reporting Agent
- **Description**: Find deals with expected_close_date in past and stage not in [won, lost]
- **Expected Outcome**: Activity or alert created for each stalled deal
- **Validation**: Check for call_made or note_added activities on stalled deals

### Integration Tasks

#### TASK-IN-001: Process inbound webhook (email)
- **Trigger**: POST /api/webhooks/email
- **Description**: Receive inbound email, create or update lead
- **Expected Outcome**: New lead created or existing lead updated with new activity
- **Validation**: Check lead exists with email source and recent activity

## Running Tasks

QA can run these tasks by:
1. Manually triggering agent via UI
2. Using API to create activities that agents will pick up
3. Using Celery task queue directly for testing

## Expected Test Coverage

| Task Type | Coverage Area |
|-----------|---------------|
| Lead Sourcing | API endpoints, model creation |
| Outreach | Celery tasks, activity logging |
| Follow-up | Lead update logic, snooze mechanism |
| Qualification | Scoring rules, stage transitions |
| Reporting | Dashboard stats, deal tracking |
| Integration | Webhook endpoints, data enrichment |