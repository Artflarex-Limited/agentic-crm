"""
Dashboard API routes
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from app.prisma import prisma

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    # Total counts
    total_leads = await prisma.lead.count()
    total_contacts = await prisma.contact.count()
    total_deals = await prisma.deal.count()

    # Open deals value — sum of deal values where stage not in won/lost
    all_deals = await prisma.deal.find_many(
        where={"stage": {"notIn": ["won", "lost"]}}
    )
    open_deals_value = sum(d.value or 0.0 for d in all_deals)

    # Leads by stage
    leads_by_stage = {}
    for stage in ["new", "contacted", "qualified", "proposal", "negotiation"]:
        count = await prisma.lead.count(where={"stage": stage})
        leads_by_stage[stage] = count

    # Deals by stage
    deals_by_stage = {}
    for stage in ["lead", "qualified", "proposal", "negotiation", "won", "lost"]:
        count = await prisma.deal.count(where={"stage": stage})
        deals_by_stage[stage] = count

    # Recent activities
    recent_activities = await prisma.activity.find_many(
        order={"created_at": "desc"},
        take=10,
    )

    return {
        "total_leads": total_leads,
        "total_contacts": total_contacts,
        "total_deals": total_deals,
        "open_deals_value": open_deals_value,
        "leads_by_stage": leads_by_stage,
        "deals_by_stage": deals_by_stage,
        "recent_activities": recent_activities,
    }


@router.get("/pipeline")
async def get_pipeline():
    """Kanban-style pipeline view"""
    deals = await prisma.deal.find_many(
        order={"created_at": "desc"},
        include={"contact": True, "company": True},
    )

    pipeline = {}
    for deal in deals:
        stage = deal.stage.value if hasattr(deal.stage, 'value') else deal.stage
        if stage not in pipeline:
            pipeline[stage] = []
        contact_name = ""
        if deal.contact:
            contact_name = f"{deal.contact.first_name or ''} {deal.contact.last_name or ''}".strip()
        pipeline[stage].append({
            "id": deal.id,
            "name": deal.name,
            "value": deal.value,
            "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
            "contact_name": contact_name,
            "company_name": deal.company.name if deal.company else None,
        })
    return pipeline


@router.get("/market-intelligence")
async def get_market_intelligence(
    period_days: int = Query(default=30, ge=7, le=365),
):
    """Market Intelligence Dashboard - conversion metrics, forecasts, source effectiveness."""
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)

    # Leads grouped by stage
    all_leads = await prisma.lead.find_many()
    leads_by_stage = {}
    for lead in all_leads:
        stage = lead.stage.value if hasattr(lead.stage, 'value') else lead.stage
        leads_by_stage[stage] = leads_by_stage.get(stage, 0) + 1

    # Deals grouped by stage
    all_deals = await prisma.deal.find_many()
    deals_by_stage = {}
    for deal in all_deals:
        stage = deal.stage.value if hasattr(deal.stage, 'value') else deal.stage
        if stage not in deals_by_stage:
            deals_by_stage[stage] = {"count": 0, "value": 0.0}
        deals_by_stage[stage]["count"] += 1
        deals_by_stage[stage]["value"] += deal.value or 0.0

    new_leads_count = leads_by_stage.get("new", 0)
    contacted_leads_count = leads_by_stage.get("contacted", 0)
    qualified_leads_count = leads_by_stage.get("qualified", 0)
    proposal_leads_count = leads_by_stage.get("proposal", 0)
    negotiation_leads_count = leads_by_stage.get("negotiation", 0)
    won_leads_count = leads_by_stage.get("won", 0)

    lead_to_contacted_rate = (contacted_leads_count / new_leads_count * 100) if new_leads_count > 0 else 0.0
    contacted_to_qualified_rate = (qualified_leads_count / contacted_leads_count * 100) if contacted_leads_count > 0 else 0.0
    qualified_to_proposal_rate = (proposal_leads_count / qualified_leads_count * 100) if qualified_leads_count > 0 else 0.0
    proposal_to_negotiation_rate = (negotiation_leads_count / proposal_leads_count * 100) if proposal_leads_count > 0 else 0.0
    negotiation_to_won_rate = (won_leads_count / negotiation_leads_count * 100) if negotiation_leads_count > 0 else 0.0
    overall_conversion_rate = (won_leads_count / new_leads_count * 100) if new_leads_count > 0 else 0.0

    conversion_metrics = {
        "lead_to_contacted_rate": round(lead_to_contacted_rate, 2),
        "contacted_to_qualified_rate": round(contacted_to_qualified_rate, 2),
        "qualified_to_proposal_rate": round(qualified_to_proposal_rate, 2),
        "proposal_to_negotiation_rate": round(proposal_to_negotiation_rate, 2),
        "negotiation_to_won_rate": round(negotiation_to_won_rate, 2),
        "overall_conversion_rate": round(overall_conversion_rate, 2),
    }

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

    revenue_forecast = {
        "projected_revenue_30_days": round(projected_30, 2),
        "projected_revenue_60_days": round(projected_60, 2),
        "projected_revenue_90_days": round(projected_90, 2),
        "weighted_pipeline_value": round(weighted_pipeline_value, 2),
        "forecast_confidence": round(forecast_confidence, 2),
    }

    # Source effectiveness
    source_results = {}
    for lead in all_leads:
        if lead.created_at and lead.created_at >= cutoff_date:
            source = lead.source.value if hasattr(lead.source, 'value') else str(lead.source)
            if source not in source_results:
                source_results[source] = {"count": 0, "total_score": 0}
            source_results[source]["count"] += 1
            source_results[source]["total_score"] += lead.score or 0

    source_effectiveness = []
    for source, data in source_results.items():
        count = data["count"]

        # Count converted leads (qualified through won stages)
        source_leads = [
            lead for lead in all_leads
            if (lead.source.value if hasattr(lead.source, 'value') else str(lead.source)) == source
            and (lead.stage.value if hasattr(lead.stage, 'value') else str(lead.stage)) in ["qualified", "proposal", "negotiation", "won"]
        ]
        converted = len(source_leads)
        source_conversion = (converted / count * 100) if count > 0 else 0.0

        # Revenue from deals via contacts
        source_revenue = 0.0
        for lead in source_leads:
            if lead.contact_id:
                contact_deals = await prisma.deal.find_many(
                    where={"contact_id": lead.contact_id}
                )
                for d in contact_deals:
                    source_revenue += d.value or 0.0

        source_effectiveness.append({
            "source": source,
            "total_leads": count,
            "conversion_rate": round(source_conversion, 2),
            "avg_deal_value": round(source_revenue / count, 2) if count > 0 else 0.0,
            "revenue": round(source_revenue, 2),
        })

    # Agent performance
    agents = await prisma.agent.find_many(where={"status": "active"})
    agent_performance = []
    for agent in agents:
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        week_start = datetime.utcnow() - timedelta(days=7)

        today_actions = await prisma.activity.count(
            where={
                "agent_id": agent.id,
                "created_at": {"gte": today_start},
            }
        )
        week_actions = await prisma.activity.count(
            where={
                "agent_id": agent.id,
                "created_at": {"gte": week_start},
            }
        )

        agent_performance.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "actions_today": today_actions,
            "actions_this_week": week_actions,
            "success_rate": 75.0,
            "avg_response_time_minutes": 45.0,
        })

    return {
        "conversion_metrics": conversion_metrics,
        "revenue_forecast": revenue_forecast,
        "source_effectiveness": source_effectiveness,
        "agent_performance": agent_performance,
        "period_days": period_days,
    }
