"""
Dashboard API routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Activity, Contact, Deal, Lead
from app.schemas.schemas import DashboardStats

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
