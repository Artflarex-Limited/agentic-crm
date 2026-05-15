"""
Supplier Matching Agent

AI agent that matches buyer RFQ requirements to verified suppliers.
Part of the outreach/turkey-eu-suppliers supplier network initiative.

Tasks:
- match_rfq_to_suppliers: Find best suppliers for an incoming RFQ
- score_supplier_matches: Score and rank supplier matches
- notify_suppliers: Notify matched suppliers of new RFQ opportunities
"""
import logging
from datetime import datetime

from sqlalchemy import select

from app.agents._async import run_async
from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.celery_app import celery_app
from app.db.database import get_async_session_local
from app.models.models import AgentRole, AuditLog, Lead, LeadSource, Supplier, SupplierStatus
from app.services.supplier_matching_service import SupplierMatchingService, get_supplier_matching_service

logger = logging.getLogger(__name__)

supplier_matching_service = SupplierMatchingService()


@celery_app.task(
    name="agents.supplier_matching.match_rfq_to_suppliers",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def match_rfq_to_suppliers(
    self,
    lead_id: int | None = None,
    rfq_industry: str | None = None,
    rfq_categories: list | None = None,
    rfq_countries: list | None = None,
    top_n: int = 10,
    correlation_id: str | None = None,
):
    """
    Match an RFQ (lead) to best-fit suppliers from the verified network.

    Can be called with either lead_id (to get RFQ data from lead) or
    directly with rfq_industry/rfq_categories for direct matching.

    Args:
        lead_id: Lead ID to extract RFQ data from
        rfq_industry: Industry category for RFQ
        rfq_categories: Product categories needed
        rfq_countries: Preferred countries
        top_n: Number of top matches to return
        correlation_id: For distributed tracing

    Returns:
        Dict with match results and supplier IDs
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Starting supplier matching: lead_id={lead_id}, industry={rfq_industry}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _match_rfq():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            industry = rfq_industry
            categories = rfq_categories or []

            if lead_id:
                result = await db.execute(
                    select(Lead).where(Lead.id == lead_id)
                )
                lead = result.scalar_one_or_none()
                if not lead:
                    logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
                    return {"status": "error", "message": "Lead not found"}

                lead_notes = lead.notes or ""
                industry = industry or lead.notes.split()[0] if lead.notes else "general"

                if lead.tags:
                    categories = [tag for tag in lead.tags if isinstance(tag, str)]

            if not industry:
                return {"status": "error", "message": "No RFQ industry specified"}

            matches = await supplier_matching_service.get_top_suppliers_for_rfq(
                rfq_industry=industry,
                rfq_categories=categories,
                rfq_countries=rfq_countries,
                top_n=top_n,
            )

            for match in matches:
                await supplier_matching_service.record_match_event(
                    supplier_id=match.supplier_id,
                    rfq_industry=industry,
                    match_score=match.match_score,
                    event_type="rfq_matched",
                )

            audit = AuditLog(
                action="rfq_matched_to_suppliers",
                entity_type="lead" if lead_id else "rfq",
                entity_id=lead_id or 0,
                details={
                    "industry": industry,
                    "categories": categories,
                    "match_count": len(matches),
                    "top_matches": [
                        {"supplier_id": m.supplier_id, "score": m.match_score}
                        for m in matches[:5]
                    ],
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(
                f"RFQ matched to {len(matches)} suppliers: industry={industry}",
                extra={"run_id": run_id, "match_count": len(matches)}
            )
            return {
                "status": "matched",
                "industry": industry,
                "match_count": len(matches),
                "matches": [
                    {
                        "supplier_id": m.supplier_id,
                        "company_name": m.company_name,
                        "country": m.country,
                        "match_score": m.match_score,
                        "match_reasons": m.match_reasons,
                        "certifications": m.certifications,
                        "production_capacity": m.production_capacity,
                        "exporting_to_eu": m.exporting_to_eu,
                    }
                    for m in matches
                ],
            }

    return run_async(_match_rfq())


@celery_app.task(
    name="agents.supplier_matching.score_supplier_matches",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def score_supplier_matches(
    self,
    supplier_ids: list[int],
    rfq_industry: str,
    rfq_categories: list | None = None,
    required_certifications: list | None = None,
    correlation_id: str | None = None,
):
    """
    Score and rank a list of suppliers for an RFQ.

    Args:
        supplier_ids: List of supplier IDs to score
        rfq_industry: Industry category
        rfq_categories: Product categories
        required_certifications: Required certifications
        correlation_id: For distributed tracing

    Returns:
        Dict with scored results
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Scoring {len(supplier_ids)} supplier matches for industry={rfq_industry}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _score_matches():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Supplier).where(Supplier.id.in_(supplier_ids))
            )
            suppliers = result.scalars().all()

            if not suppliers:
                logger.warning(f"No suppliers found for IDs: {supplier_ids}", extra={"run_id": run_id})
                return {"status": "error", "message": "No suppliers found"}

            scored_results = []
            for supplier in suppliers:
                score, reasons = supplier_matching_service._calculate_match_score(
                    supplier=supplier,
                    required_industry=rfq_industry,
                    required_categories=rfq_categories or [],
                    required_certifications=required_certifications or [],
                )
                scored_results.append({
                    "supplier_id": supplier.id,
                    "company_name": supplier.company_name,
                    "country": supplier.country,
                    "industry": supplier.industry,
                    "score": score,
                    "reasons": reasons,
                    "certifications": supplier.certifications or [],
                    "production_capacity": supplier.production_capacity,
                })

            scored_results.sort(key=lambda x: x["score"], reverse=True)

            logger.info(
                f"Scored {len(scored_results)} suppliers",
                extra={"run_id": run_id, "count": len(scored_results)}
            )
            return {
                "status": "scored",
                "count": len(scored_results),
                "results": scored_results,
            }

    return run_async(_score_matches())


@celery_app.task(
    name="agents.supplier_matching.notify_suppliers",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def notify_suppliers(
    self,
    supplier_ids: list[int],
    rfq_industry: str,
    rfq_description: str | None = None,
    correlation_id: str | None = None,
):
    """
    Notify matched suppliers about a new RFQ opportunity.

    Args:
        supplier_ids: List of supplier IDs to notify
        rfq_industry: Industry for the RFQ
        rfq_description: Description of the RFQ
        correlation_id: For distributed tracing

    Returns:
        Dict with notification status
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Notifying {len(supplier_ids)} suppliers about RFQ: {rfq_industry}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _notify():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Supplier).where(Supplier.id.in_(supplier_ids))
            )
            suppliers = result.scalars().all()

            notified = []
            for supplier in suppliers:
                if supplier.status == SupplierStatus.VERIFIED:
                    notified.append({
                        "supplier_id": supplier.id,
                        "company_name": supplier.company_name,
                        "email": supplier.business_email,
                        "status": "notified",
                    })

                    audit = AuditLog(
                        action="supplier_notified",
                        entity_type="supplier",
                        entity_id=supplier.id,
                        details={
                            "rfq_industry": rfq_industry,
                            "rfq_description": rfq_description,
                            "notification_type": "rfq_opportunity",
                            "run_id": run_id,
                            "correlation_id": corr_id,
                        },
                    )
                    db.add(audit)

            await db.commit()
            logger.info(
                f"Notified {len(notified)} suppliers",
                extra={"run_id": run_id, "count": len(notified)}
            )
            return {
                "status": "notified",
                "count": len(notified),
                "suppliers": notified,
            }

    return run_async(_notify())


@celery_app.task(
    name="agents.supplier_matching.verify_supplier",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def verify_supplier(
    self,
    supplier_id: int,
    correlation_id: str | None = None,
):
    """
    Verify a supplier for the network.

    Args:
        supplier_id: Supplier ID to verify
        correlation_id: For distributed tracing

    Returns:
        Dict with verification status
    """
    run_id = get_current_run_id()
    corr_id = correlation_id or get_current_correlation_id()
    AgentContext(role=AgentRole.OUTREACH)

    logger.info(
        f"Verifying supplier: supplier_id={supplier_id}",
        extra={"run_id": run_id, "correlation_id": corr_id, "task_name": self.name}
    )

    async def _verify():
        SessionLocal = get_async_session_local()
        if SessionLocal is None:
            logger.error("Database not configured", extra={"run_id": run_id})
            return {"status": "error", "message": "Database not configured"}

        async with SessionLocal() as db:
            result = await db.execute(
                select(Supplier).where(Supplier.id == supplier_id)
            )
            supplier = result.scalar_one_or_none()
            if not supplier:
                logger.warning(f"Supplier not found: {supplier_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Supplier not found"}

            supplier.status = SupplierStatus.VERIFIED
            supplier.verified_at = datetime.utcnow()

            audit = AuditLog(
                action="supplier_verified",
                entity_type="supplier",
                entity_id=supplier_id,
                details={
                    "company_name": supplier.company_name,
                    "country": supplier.country,
                    "verified_at": datetime.utcnow().isoformat(),
                    "run_id": run_id,
                    "correlation_id": corr_id,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(
                f"Supplier verified: {supplier.company_name}",
                extra={"run_id": run_id, "supplier_id": supplier_id}
            )
            return {
                "status": "verified",
                "supplier_id": supplier_id,
                "company_name": supplier.company_name,
            }

    return run_async(_verify())