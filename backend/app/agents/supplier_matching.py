"""
Supplier Matching Agent

AI agent that matches buyer RFQ requirements to verified suppliers.
Part of the outreach/turkey-eu-suppliers supplier network initiative.

Tasks:
- match_rfq_to_suppliers: Find best suppliers for an incoming RFQ
- score_supplier_matches: Score and rank supplier matches
- notify_suppliers: Notify matched suppliers of new RFQ opportunities
"""
import json
import logging
from datetime import datetime

from app.agents.context import AgentContext, get_current_correlation_id, get_current_run_id
from app.models import AgentRole
from app.prisma import prisma
from app.services.supplier_matching_service import SupplierMatchingService, get_supplier_matching_service

logger = logging.getLogger(__name__)

supplier_matching_service = SupplierMatchingService()


async def match_rfq_to_suppliers(
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
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        industry = rfq_industry
        categories = rfq_categories or []

        if lead_id:
            lead = await prisma.lead.find_unique(where={"id": lead_id})
            if not lead:
                logger.warning(f"Lead not found: {lead_id}", extra={"run_id": run_id})
                return {"status": "error", "message": "Lead not found"}

            lead_notes = lead.notes or ""
            industry = industry or lead_notes.split()[0] if lead_notes else "general"

            if lead.tags:
                tags = json.loads(lead.tags) if isinstance(lead.tags, str) else lead.tags
                categories = [tag for tag in tags if isinstance(tag, str)]

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

        await prisma.auditlog.create(
            data={
                "action": "rfq_matched_to_suppliers",
                "entityType": "lead" if lead_id else "rfq",
                "entityId": lead_id or 0,
                "details": json.dumps({
                    "industry": industry,
                    "categories": categories,
                    "match_count": len(matches),
                    "top_matches": [
                        {"supplier_id": m.supplier_id, "score": m.match_score}
                        for m in matches[:5]
                    ],
                    "run_id": run_id,
                    "correlation_id": corr_id,
                }),
            }
        )

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
    except Exception as e:
        logger.error(f"Error matching RFQ to suppliers: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}


async def score_supplier_matches(
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
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        suppliers = await prisma.supplier.find_many(
            where={"id": {"in": supplier_ids}}
        )

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
                "company_name": supplier.companyName,
                "country": supplier.country,
                "industry": supplier.industry,
                "score": score,
                "reasons": reasons,
                "certifications": json.loads(supplier.certifications) if supplier.certifications else [],
                "production_capacity": supplier.productionCapacity,
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
    except Exception as e:
        logger.error(f"Error scoring supplier matches: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}


async def notify_suppliers(
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
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        suppliers = await prisma.supplier.find_many(
            where={"id": {"in": supplier_ids}}
        )

        notified = []
        for supplier in suppliers:
            if supplier.status == "VERIFIED":
                notified.append({
                    "supplier_id": supplier.id,
                    "company_name": supplier.companyName,
                    "email": supplier.businessEmail,
                    "status": "notified",
                })

                await prisma.auditlog.create(
                    data={
                        "action": "supplier_notified",
                        "entityType": "supplier",
                        "entityId": supplier.id,
                        "details": json.dumps({
                            "rfq_industry": rfq_industry,
                            "rfq_description": rfq_description,
                            "notification_type": "rfq_opportunity",
                            "run_id": run_id,
                            "correlation_id": corr_id,
                        }),
                    }
                )

        logger.info(
            f"Notified {len(notified)} suppliers",
            extra={"run_id": run_id, "count": len(notified)}
        )
        return {
            "status": "notified",
            "count": len(notified),
            "suppliers": notified,
        }
    except Exception as e:
        logger.error(f"Error notifying suppliers: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}


async def verify_supplier(
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
        extra={"run_id": run_id, "correlation_id": corr_id}
    )

    try:
        supplier = await prisma.supplier.find_unique(where={"id": supplier_id})
        if not supplier:
            logger.warning(f"Supplier not found: {supplier_id}", extra={"run_id": run_id})
            return {"status": "error", "message": "Supplier not found"}

        supplier = await prisma.supplier.update(
            where={"id": supplier_id},
            data={
                "status": "VERIFIED",
                "verifiedAt": datetime.utcnow().isoformat(),
            }
        )

        await prisma.auditlog.create(
            data={
                "action": "supplier_verified",
                "entityType": "supplier",
                "entityId": supplier_id,
                "details": json.dumps({
                    "company_name": supplier.companyName,
                    "country": supplier.country,
                    "verified_at": datetime.utcnow().isoformat(),
                    "run_id": run_id,
                    "correlation_id": corr_id,
                }),
            }
        )

        logger.info(
            f"Supplier verified: {supplier.companyName}",
            extra={"run_id": run_id, "supplier_id": supplier_id}
        )
        return {
            "status": "verified",
            "supplier_id": supplier_id,
            "company_name": supplier.companyName,
        }
    except Exception as e:
        logger.error(f"Error verifying supplier: {e}", extra={"run_id": run_id})
        return {"status": "error", "message": str(e)}
