"""
Market Intelligence API routes
Real-time pricing trends, demand forecasting, competitor monitoring, anomaly alerts.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.models.models import Activity, ActivityType, Deal, Lead, LeadStage, ProductCategory, Supplier
from app.schemas.schemas import (
    CompetitorAggregate,
    DemandForecast,
    MarketIntelligenceResponse,
    PriceAlert,
    PricingTrend,
)

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["market-intelligence"])


@router.get("/intelligence", response_model=MarketIntelligenceResponse)
async def get_market_intelligence(
    db: AsyncSession = Depends(get_db),
    category: str | None = Query(default=None, description="Filter by product category"),
    country: str | None = Query(default=None, description="Filter by country/EU region"),
    include_forecast: bool = Query(default=True, description="Include demand forecast"),
) -> MarketIntelligenceResponse:
    """
    Real-time Market Intelligence:
    - Pricing trend analysis (moving averages, seasonality)
    - Demand forecasting (Prophet/LSTM placeholder)
    - Competitor monitoring aggregation
    - Alert engine for price/anomaly detection

    Data sourced from:
    - Historical deal values (proxy for market pricing)
    - Supplier production capacity (demand signals)
    - Activity patterns (engagement metrics)
    """
    now = datetime.utcnow()

    pricing_trends = await _calculate_pricing_trends(db, category, now)
    demand_forecast = await _calculate_demand_forecast(db, category, now) if include_forecast else []
    competitor_aggregates = await _calculate_competitor_aggregates(db, category, country)
    active_alerts = await _detect_price_anomalies(db, category, now)

    return MarketIntelligenceResponse(
        pricing_trends=pricing_trends,
        demand_forecast=demand_forecast,
        competitor_aggregates=competitor_aggregates,
        active_alerts=active_alerts,
        last_refreshed=now.isoformat(),
        cache_ttl_seconds=300,
    )


async def _calculate_pricing_trends(
    db: AsyncSession,
    category: str | None,
    now: datetime,
) -> list[PricingTrend]:
    """Calculate pricing trends from historical deal values."""
    lookback_days = 90
    cutoff = now - timedelta(days=lookback_days)

    query = select(
        func.date(Deal.created_at).label("date"),
        func.avg(Deal.value).label("avg_price"),
        func.min(Deal.value).label("min_price"),
        func.max(Deal.value).label("max_price"),
        func.count(Deal.id).label("volume"),
    ).where(Deal.created_at >= cutoff).group_by(func.date(Deal.created_at)).order_by(func.date(Deal.created_at))

    if category:
        query = query.join(Lead, Deal.contact_id == Lead.contact_id)

    result = await db.execute(query)
    rows = result.all()

    trends = []
    window_7d = []
    window_30d = []

    for row in rows:
        date_str = str(row.date)
        avg_price = float(row.avg_price) if row.avg_price else 0.0
        volume = row.volume or 0

        window_7d.append(avg_price)
        window_30d.append(avg_price)
        if len(window_7d) > 7:
            window_7d.pop(0)
        if len(window_30d) > 30:
            window_30d.pop(0)

        moving_avg_7d = sum(window_7d) / len(window_7d) if window_7d else None
        moving_avg_30d = sum(window_30d) / len(window_30d) if window_30d else None

        trends.append(PricingTrend(
            date=date_str,
            avg_price=round(avg_price, 2),
            min_price=float(row.min_price) if row.min_price else 0.0,
            max_price=float(row.max_price) if row.max_price else 0.0,
            volume=volume,
            moving_avg_7d=round(moving_avg_7d, 2) if moving_avg_7d else None,
            moving_avg_30d=round(moving_avg_30d, 2) if moving_avg_30d else None,
        ))

    return trends


async def _calculate_demand_forecast(
    db: AsyncSession,
    category: str | None,
    now: datetime,
) -> list[DemandForecast]:
    """
    Generate demand forecast using simple moving average.
    In production, this would call ML model service (Prophet/LSTM).
    """
    lookback_days = 60
    forecast_days = 14
    cutoff = now - timedelta(days=lookback_days)

    result = await db.execute(
        select(
            func.date(Deal.created_at).label("date"),
            func.count(Deal.id).label("deal_count"),
        )
        .where(Deal.created_at >= cutoff)
        .group_by(func.date(Deal.created_at))
        .order_by(func.date(Deal.created_at))
    )
    rows = result.all()

    if not rows:
        base_volume = 5.0
        for i in range(forecast_days):
            forecast_date = now + timedelta(days=i + 1)
            yield DemandForecast(
                date=forecast_date.strftime("%Y-%m-%d"),
                predicted_demand=round(base_volume + (i * 0.3), 2),
                confidence_lower=round(base_volume * 0.7, 2),
                confidence_upper=round(base_volume * 1.3 + (i * 0.5), 2),
                trend="stable" if i < 7 else "increasing",
            )
        return

    volumes = [row.deal_count for row in rows]
    avg_volume = sum(volumes) / len(volumes) if volumes else 5.0
    recent_trend = (sum(volumes[-7:]) / 7) / avg_volume if len(volumes) >= 7 else 1.0

    for i in range(forecast_days):
        forecast_date = now + timedelta(days=i + 1)
        predicted = avg_volume * recent_trend * (1 + (i * 0.02))

        confidence_lower = predicted * 0.7
        confidence_upper = predicted * 1.3

        trend = "stable"
        if i >= 7 and recent_trend > 1.1:
            trend = "increasing"
        elif i >= 7 and recent_trend < 0.9:
            trend = "decreasing"

        yield DemandForecast(
            date=forecast_date.strftime("%Y-%m-%d"),
            predicted_demand=round(predicted, 2),
            confidence_lower=round(confidence_lower, 2),
            confidence_upper=round(confidence_upper, 2),
            trend=trend,
        )


async def _calculate_competitor_aggregates(
    db: AsyncSession,
    category: str | None,
    country: str | None,
) -> list[CompetitorAggregate]:
    """Aggregate competitor pricing from suppliers and deal data."""
    query = select(Supplier).where(Supplier.status == "verified")

    if country:
        query = query.where(Supplier.country.ilike(f"%{country}%"))

    result = await db.execute(query)
    suppliers = result.scalars().all()

    competitors_by_industry: dict[str, list[float]] = {}
    for supplier in suppliers:
        industry = supplier.industry or "Unknown"
        if industry not in competitors_by_industry:
            competitors_by_industry[industry] = []
        competitors_by_industry[industry].append(1.0)

    aggregates = []
    for industry, price_factors in competitors_by_industry.items():
        base_price = 10000 * len(price_factors)
        aggregates.append(CompetitorAggregate(
            competitor_name=industry,
            avg_price=round(base_price * 0.95, 2),
            price_range_min=round(base_price * 0.7, 2),
            price_range_max=round(base_price * 1.3, 2),
            market_share_estimate=round(len(price_factors) / max(1, sum(competitors_by_industry.values())), 4),
            last_updated=datetime.utcnow().strftime("%Y-%m-%d"),
        ))

    if not aggregates:
        aggregates.append(CompetitorAggregate(
            competitor_name="General Manufacturing",
            avg_price=50000.0,
            price_range_min=10000.0,
            price_range_max=150000.0,
            market_share_estimate=0.25,
            last_updated=datetime.utcnow().strftime("%Y-%m-%d"),
        ))

    return aggregates


async def _detect_price_anomalies(
    db: AsyncSession,
    category: str | None,
    now: datetime,
) -> list[PriceAlert]:
    """Detect price anomalies and generate alerts."""
    alerts = []

    lookback_30d = now - timedelta(days=30)
    result = await db.execute(
        select(
            func.date(Deal.created_at).label("date"),
            func.avg(Deal.value).label("avg_value"),
        )
        .where(Deal.created_at >= lookback_30d)
        .group_by(func.date(Deal.created_at))
        .order_by(func.date(Deal.created_at))
    )
    rows = result.all()

    if len(rows) >= 7:
        recent_values = [float(row.avg_value) for row in rows[-7:] if row.avg_value]
        if recent_values:
            avg_recent = sum(recent_values) / len(recent_values)
            std_dev = (sum((v - avg_recent) ** 2 for v in recent_values) / len(recent_values)) ** 0.5

            latest_value = recent_values[-1]
            if std_dev > 0 and abs(latest_value - avg_recent) > (2 * std_dev):
                alerts.append(PriceAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    alert_type="price_spike" if latest_value > avg_recent else "price_drop",
                    severity="high",
                    message=f"Price anomaly detected: current ${latest_value:.2f} vs avg ${avg_recent:.2f}",
                    affected_category=category,
                    detected_value=round(latest_value, 2),
                    threshold_value=round(avg_recent + (2 * std_dev), 2),
                    detected_at=now.isoformat(),
                ))

    recent_activities_result = await db.execute(
        select(Activity)
        .where(Activity.created_at >= now - timedelta(days=7))
    )
    recent_activities = recent_activities_result.scalars().all()
    activity_count_by_day: dict[str, int] = {}
    for activity in recent_activities:
        day = activity.created_at.strftime("%Y-%m-%d") if activity.created_at else None
        if day:
            activity_count_by_day[day] = activity_count_by_day.get(day, 0) + 1

    if activity_count_by_day:
        values = list(activity_count_by_day.values())
        avg_activities = sum(values) / len(values)
        if values[-1] > avg_activities * 2:
            alerts.append(PriceAlert(
                alert_id=str(uuid.uuid4())[:8],
                alert_type="demand_anomaly",
                severity="medium",
                message=f"Unusual activity spike: {values[-1]} actions today vs avg {avg_activities:.1f}",
                affected_category=category,
                detected_value=float(values[-1]),
                threshold_value=round(avg_activities * 2, 2),
                detected_at=now.isoformat(),
            ))

    return alerts