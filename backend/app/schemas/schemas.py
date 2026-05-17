"""
Pydantic schemas for request/response validation
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums import ActivityType, AgentRole, AgentStatus, DealStage, LeadSource, LeadStage


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

    model_config = ConfigDict(from_attributes=True)


# ─── Contact ──────────────────────────────────────────────────────────────────
class ContactCreate(BaseModel):
    company_id: int | None = Field(default=None, validation_alias="companyId")
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    extra_data: dict = {}

    model_config = ConfigDict(populate_by_name=True)


class ContactResponse(ContactCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Lead ────────────────────────────────────────────────────────────────────
class LeadCreate(BaseModel):
    contact_id: int = Field(validation_alias="contactId")
    source: LeadSource = LeadSource.OTHER
    stage: LeadStage = LeadStage.NEW
    score: int = 0
    tags: list = []
    notes: str | None = None
    assigned_agent_id: int | None = None

    class Config:
        populate_by_name = True


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

    model_config = ConfigDict(from_attributes=True)


# ─── Deal ────────────────────────────────────────────────────────────────────
class DealCreate(BaseModel):
    contact_id: int = Field(validation_alias="contactId")
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

    model_config = ConfigDict(from_attributes=True)


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


# ─── Market Intelligence ──────────────────────────────────────────────────────
class ConversionMetrics(BaseModel):
    lead_to_contacted_rate: float
    contacted_to_qualified_rate: float
    qualified_to_proposal_rate: float
    proposal_to_negotiation_rate: float
    negotiation_to_won_rate: float
    overall_conversion_rate: float


class RevenueForecast(BaseModel):
    projected_revenue_30_days: float
    projected_revenue_60_days: float
    projected_revenue_90_days: float
    weighted_pipeline_value: float
    forecast_confidence: float


class SourceEffectiveness(BaseModel):
    source: str
    total_leads: int
    conversion_rate: float
    avg_deal_value: float
    revenue: float


class AgentPerformanceMetric(BaseModel):
    agent_id: int
    agent_name: str
    actions_today: int
    actions_this_week: int
    success_rate: float
    avg_response_time_minutes: float


class MarketIntelligenceDashboard(BaseModel):
    conversion_metrics: ConversionMetrics
    revenue_forecast: RevenueForecast
    source_effectiveness: list[SourceEffectiveness]
    agent_performance: list[AgentPerformanceMetric]
    period_days: int


# ─── Market Intelligence (Real-time) ─────────────────────────────────────────
class PricingTrend(BaseModel):
    date: str
    avg_price: float
    min_price: float
    max_price: float
    volume: int
    moving_avg_7d: float | None
    moving_avg_30d: float | None


class DemandForecast(BaseModel):
    date: str
    predicted_demand: float
    confidence_lower: float
    confidence_upper: float
    trend: str  # "increasing", "decreasing", "stable"


class CompetitorAggregate(BaseModel):
    competitor_name: str
    avg_price: float
    price_range_min: float
    price_range_max: float
    market_share_estimate: float
    last_updated: str


class PriceAlert(BaseModel):
    alert_id: str
    alert_type: str  # "price_spike", "price_drop", "demand_anomaly", "competitor_movement"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    affected_category: str | None
    detected_value: float
    threshold_value: float
    detected_at: str


class MarketIntelligenceResponse(BaseModel):
    pricing_trends: list[PricingTrend]
    demand_forecast: list[DemandForecast]
    competitor_aggregates: list[CompetitorAggregate]
    active_alerts: list[PriceAlert]
    last_refreshed: str
    cache_ttl_seconds: int
