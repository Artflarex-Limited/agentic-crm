"""
Dashboard API routes
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Activity, ActivityType, Contact, Deal, Lead, LeadStage, Agent
from app.schemas.schemas import (
    AgentPerformanceMetric,
    ConversionMetrics,
    DashboardStats,
    MarketIntelligenceDashboard,
    PipelineItem,
    RevenueForecast,
    SourceEffectiveness,
)

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Total counts
    total_leads = await db.execute(select(func.count(Lead.id)))
    total_contacts = await db.execute(select(func.count(Contact.id)))
    total_deals = await db.execute(select(func.count(Deal.id)))

    # Open deals value
    open_deals_result = await db.execute(
        select(func.sum(Deal.value)).where(Deal.stage.notin_(["won", "lost"]))
    )
    open_deals_value = open_deals_result.scalar() or 0.0

    # Leads by stage
    leads_by_stage = {}
    for stage in ["new", "contacted", "qualified", "proposal", "negotiation"]:
        count = await db.execute(select(func.count(Lead.id)).where(Lead.stage == stage))
        leads_by_stage[stage] = count.scalar() or 0

    # Deals by stage
    deals_by_stage = {}
    for stage in ["lead", "qualified", "proposal", "negotiation", "won", "lost"]:
        count = await db.execute(select(func.count(Deal.id)).where(Deal.stage == stage))
        deals_by_stage[stage] = count.scalar() or 0

    # Recent activities
    recent_result = await db.execute(
        select(Activity).order_by(Activity.created_at.desc()).limit(10)
    )
    recent_activities = recent_result.scalars().all()

    return DashboardStats(
        total_leads=total_leads.scalar() or 0,
        total_contacts=total_contacts.scalar() or 0,
        total_deals=total_deals.scalar() or 0,
        open_deals_value=open_deals_value,
        leads_by_stage=leads_by_stage,
        deals_by_stage=deals_by_stage,
        recent_activities=recent_activities,
    )


@router.get("/pipeline")
async def get_pipeline(db: AsyncSession = Depends(get_db)):
    """Kanban-style pipeline view"""
    result = await db.execute(
        select(Deal).order_by(Deal.created_at.desc())
    )
    deals = result.scalars().all()

    pipeline = {}
    for deal in deals:
        stage = deal.stage.value if hasattr(deal.stage, 'value') else deal.stage
        if stage not in pipeline:
            pipeline[stage] = []
        pipeline[stage].append({
            "id": deal.id,
            "name": deal.name,
            "value": deal.value,
            "expected_close_date": deal.expected_close_date,
            "contact_name": deal.contact.first_name + " " + deal.contact.last_name if deal.contact else "",
            "company_name": deal.company.name if deal.company else None,
        })
    return pipeline


@router.get("/market-intelligence", response_model=MarketIntelligenceDashboard)
async def get_market_intelligence(
    db: AsyncSession = Depends(get_db),
    period_days: int = Query(default=30, ge=7, le=365),
):
    """Market Intelligence Dashboard - conversion metrics, forecasts, source effectiveness."""
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)

    leads_by_stage_result = await db.execute(select(Lead.stage, func.count(Lead.id)).group_by(Lead.stage))
    leads_by_stage = dict(leads_by_stage_result.all())

    deals_result = await db.execute(
        select(Deal.stage, func.count(Deal.id), func.sum(Deal.value)).group_by(Deal.stage)
    )
    deals_by_stage = {stage: {"count": count, "value": value or 0.0} for stage, count, value in deals_result.all()}

    new_leads_count = leads_by_stage.get(LeadStage.NEW, 0)
    contacted_leads_count = leads_by_stage.get(LeadStage.CONTACTED, 0)
    qualified_leads_count = leads_by_stage.get(LeadStage.QUALIFIED, 0)
    proposal_leads_count = leads_by_stage.get(LeadStage.PROPOSAL, 0)
    negotiation_leads_count = leads_by_stage.get(LeadStage.NEGOTIATION, 0)
    won_leads_count = leads_by_stage.get(LeadStage.WON, 0)

    lead_to_contacted_rate = (contacted_leads_count / new_leads_count * 100) if new_leads_count > 0 else 0.0
    contacted_to_qualified_rate = (qualified_leads_count / contacted_leads_count * 100) if contacted_leads_count > 0 else 0.0
    qualified_to_proposal_rate = (proposal_leads_count / qualified_leads_count * 100) if qualified_leads_count > 0 else 0.0
    proposal_to_negotiation_rate = (negotiation_leads_count / proposal_leads_count * 100) if proposal_leads_count > 0 else 0.0
    negotiation_to_won_rate = (won_leads_count / negotiation_leads_count * 100) if negotiation_leads_count > 0 else 0.0
    overall_conversion_rate = (won_leads_count / new_leads_count * 100) if new_leads_count > 0 else 0.0

    conversion_metrics = ConversionMetrics(
        lead_to_contacted_rate=round(lead_to_contacted_rate, 2),
        contacted_to_qualified_rate=round(contacted_to_qualified_rate, 2),
        qualified_to_proposal_rate=round(qualified_to_proposal_rate, 2),
        proposal_to_negotiation_rate=round(proposal_to_negotiation_rate, 2),
        negotiation_to_won_rate=round(negotiation_to_won_rate, 2),
        overall_conversion_rate=round(overall_conversion_rate, 2),
    )

    active_deals_count = sum(
        deals_by_stage.get(stage, {}).get("count", 0)
        for stage in ["lead", "qualified", "proposal", "negotiation"]
    )
    active_deals_value = sum(
        deals_by_stage.get(stage, {}).get("value", 0.0)
        for stage in ["lead", "qualified", "proposal", "negotiation"]
    )

    pipeline_velocity = 0.3
    projected_30 = active_deals_value * 0.15 * pipeline_velocity
    projected_60 = active_deals_value * 0.35 * pipeline_velocity
    projected_90 = active_deals_value * 0.55 * pipeline_velocity
    weighted_pipeline_value = active_deals_value
    forecast_confidence = 0.65 if active_deals_count > 10 else 0.45

    revenue_forecast = RevenueForecast(
        projected_revenue_30_days=round(projected_30, 2),
        projected_revenue_60_days=round(projected_60, 2),
        projected_revenue_90_days=round(projected_90, 2),
        weighted_pipeline_value=round(weighted_pipeline_value, 2),
        forecast_confidence=round(forecast_confidence, 2),
    )

    source_results = await db.execute(
        select(Lead.source, func.count(Lead.id), func.avg(Lead.score))
        .where(Lead.created_at >= cutoff_date)
        .group_by(Lead.source)
    )
    source_effectiveness = []
    for source, count, avg_score in source_results.all():
        source_leads = await db.execute(
            select(Lead).where(Lead.source == source)
        )
        source_leads_list = source_leads.scalars().all()
        converted = sum(1 for l in source_leads_list if l.stage in [LeadStage.QUALIFIED, LeadStage.PROPOSAL, LeadStage.NEGOTIATION, LeadStage.WON])
        source_conversion = (converted / count * 100) if count > 0 else 0.0

        deals_from_source_result = await db.execute(
            select(func.sum(Deal.value))
            .join(Contact, Deal.contact_id == Contact.id)
            .join(Lead, Lead.contact_id == Contact.id)
            .where(Lead.source == source)
        )
        source_revenue = deals_from_source_result.scalar() or 0.0

        source_effectiveness.append(SourceEffectiveness(
            source=source.value if hasattr(source, 'value') else str(source),
            total_leads=count,
            conversion_rate=round(source_conversion, 2),
            avg_deal_value=round(source_revenue / count, 2) if count > 0 else 0.0,
            revenue=round(source_revenue, 2),
        ))

    agent_performance_result = await db.execute(
        select(Agent).where(Agent.status == "active")
    )
    agents = agent_performance_result.scalars().all()

    agent_performance = []
    for agent in agents:
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        week_start = datetime.utcnow() - timedelta(days=7)

        today_actions_result = await db.execute(
            select(func.count(Activity.id))
            .where(Activity.agent_id == agent.id)
            .where(Activity.created_at >= today_start)
        )
        today_actions = today_actions_result.scalar() or 0

        week_actions_result = await db.execute(
            select(func.count(Activity.id))
            .where(Activity.agent_id == agent.id)
            .where(Activity.created_at >= week_start)
        )
        week_actions = week_actions_result.scalar() or 0

        agent_performance.append(AgentPerformanceMetric(
            agent_id=agent.id,
            agent_name=agent.name,
            actions_today=today_actions,
            actions_this_week=week_actions,
            success_rate=75.0,
            avg_response_time_minutes=45.0,
        ))

    return MarketIntelligenceDashboard(
        conversion_metrics=conversion_metrics,
        revenue_forecast=revenue_forecast,
        source_effectiveness=source_effectiveness,
        agent_performance=agent_performance,
        period_days=period_days,
    )
