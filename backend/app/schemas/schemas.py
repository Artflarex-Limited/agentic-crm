"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.models import LeadSource, LeadStage, DealStage, AgentRole, AgentStatus, ActivityType


# ─── Company ──────────────────────────────────────────────────────────────────
class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    linkedin_url: Optional[str] = None
    extra_data: dict = {}


class CompanyResponse(CompanyCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Contact ──────────────────────────────────────────────────────────────────
class ContactCreate(BaseModel):
    company_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
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
    notes: Optional[str] = None
    assigned_agent_id: Optional[int] = None


class LeadUpdate(BaseModel):
    stage: Optional[LeadStage] = None
    score: Optional[int] = None
    tags: Optional[list] = None
    notes: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    snooze_until: Optional[datetime] = None


class LeadResponse(LeadCreate):
    id: int
    last_contacted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    contact: Optional[ContactResponse] = None

    class Config:
        from_attributes = True


# ─── Deal ────────────────────────────────────────────────────────────────────
class DealCreate(BaseModel):
    contact_id: int
    company_id: Optional[int] = None
    name: str
    value: float = 0.0
    stage: DealStage = DealStage.LEAD
    expected_close_date: Optional[datetime] = None
    notes: Optional[str] = None


class DealUpdate(BaseModel):
    stage: Optional[DealStage] = None
    value: Optional[float] = None
    expected_close_date: Optional[datetime] = None
    notes: Optional[str] = None


class DealResponse(DealCreate):
    id: int
    actual_close_date: Optional[datetime]
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
    description: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[AgentStatus] = None
    config: Optional[dict] = None


class AgentResponse(AgentCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Sequence ─────────────────────────────────────────────────────────────────
class SequenceStep(BaseModel):
    type: str  # email, linkedin, phone
    subject: Optional[str] = None
    content: str
    delay_days: int = 0


class SequenceCreate(BaseModel):
    name: str
    description: Optional[str] = None
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
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    agent_id: Optional[int] = None
    type: ActivityType
    content: Optional[str] = None
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
    company_name: Optional[str]
    value: float
    stage: DealStage
    expected_close_date: Optional[datetime]