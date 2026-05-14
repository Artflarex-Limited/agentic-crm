"""
Pydantic schemas for request/response validation
"""
from datetime import datetime

from pydantic import BaseModel

from app.models.models import ActivityType, AgentRole, AgentStatus, DealStage, LeadSource, LeadStage


# ─── Company ──────────────────────────────────────────────────────────────────
class CompanyCreate(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    linkedin_url: str | None = None
    extra_data: dict = {}


class CompanyResponse(CompanyCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Contact ──────────────────────────────────────────────────────────────────
class ContactCreate(BaseModel):
    company_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    extra_data: dict = {}


class ContactResponse(ContactCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Lead ────────────────────────────────────────────────────────────────────
class LeadCreate(BaseModel):
    contact_id: int
    source: LeadSource = LeadSource.OTHER
    stage: LeadStage = LeadStage.NEW
    score: int = 0
    tags: list = []
    notes: str | None = None
    assigned_agent_id: int | None = None


class LeadUpdate(BaseModel):
    stage: LeadStage | None = None
    score: int | None = None
    tags: list | None = None
    notes: str | None = None
    assigned_agent_id: int | None = None
    snooze_until: datetime | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    hubspot_contact_id: str | None = None
    ga_client_id: str | None = None


class LeadResponse(LeadCreate):
    id: int
    last_contacted_at: datetime | None
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    utm_term: str | None
    utm_content: str | None
    hubspot_contact_id: str | None
    ga_client_id: str | None
    created_at: datetime
    updated_at: datetime
    contact: ContactResponse | None = None

    class Config:
        from_attributes = True


# ─── Deal ────────────────────────────────────────────────────────────────────
class DealCreate(BaseModel):
    contact_id: int
    company_id: int | None = None
    name: str
    value: float = 0.0
    stage: DealStage = DealStage.LEAD
    expected_close_date: datetime | None = None
    notes: str | None = None


class DealUpdate(BaseModel):
    stage: DealStage | None = None
    value: float | None = None
    expected_close_date: datetime | None = None
    notes: str | None = None


class DealResponse(DealCreate):
    id: int
    actual_close_date: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Agent ────────────────────────────────────────────────────────────────────
class AgentCreate(BaseModel):
    name: str
    role: AgentRole
    status: AgentStatus = AgentStatus.PAUSED
    config: dict = {}
    description: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    status: AgentStatus | None = None
    config: dict | None = None


class AgentResponse(AgentCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Sequence ─────────────────────────────────────────────────────────────────
class SequenceStep(BaseModel):
    type: str  # email, linkedin, phone
    subject: str | None = None
    content: str
    delay_days: int = 0


class SequenceCreate(BaseModel):
    name: str
    description: str | None = None
    steps: list[SequenceStep] = []
    is_active: bool = True


class SequenceResponse(SequenceCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Activity ─────────────────────────────────────────────────────────────────
class ActivityCreate(BaseModel):
    lead_id: int | None = None
    contact_id: int | None = None
    deal_id: int | None = None
    agent_id: int | None = None
    type: ActivityType
    content: str | None = None
    metadata: dict = {}


class ActivityResponse(ActivityCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_leads: int
    total_contacts: int
    total_deals: int
    open_deals_value: float
    leads_by_stage: dict
    deals_by_stage: dict
    recent_activities: list[ActivityResponse]


class PipelineItem(BaseModel):
    id: int
    name: str
    contact_name: str
    company_name: str | None
    value: float
    stage: DealStage
    expected_close_date: datetime | None
