"""
AI Supplier Matching Service

Matches buyer RFQ requirements to verified suppliers using:
- Industry/category matching
- Country/location filtering (EU, Turkey)
- Capability scoring
- Production capacity verification
- Certification validation

Used by the AI agents to score and rank suppliers for RFQ responses.
"""
import json
import logging
from dataclasses import dataclass
from typing import Optional

from app.prisma import prisma

logger = logging.getLogger(__name__)


@dataclass
class SupplierMatchResult:
    supplier_id: int
    company_name: str
    country: str
    industry: str
    match_score: float
    match_reasons: list[str]
    certifications: list[str]
    production_capacity: Optional[str]
    exporting_to_eu: bool


class SupplierMatchingService:
    def __init__(self):
        self.min_match_score = 0.3

    async def find_matching_suppliers(
        self,
        required_industry: str,
        required_categories: list[str] | None = None,
        country_filter: str | None = None,
        must_export_to_eu: bool = False,
        required_certifications: list[str] | None = None,
        min_score: float = 0.3,
    ) -> list[SupplierMatchResult]:
        """
        Find suppliers matching RFQ requirements.

        Args:
            required_industry: Industry category (e.g., "Electronics", "Machinery")
            required_categories: List of product categories to match
            country_filter: Specific country or region (e.g., "Turkey", "Germany")
            must_export_to_eu: Whether supplier must already export to EU
            required_certifications: Required certifications (e.g., ["CE", "ISO 9001"])
            min_score: Minimum match score threshold

        Returns:
            List of SupplierMatchResult sorted by match_score descending
        """
        try:
            await prisma.$connect()
        except Exception:
            pass

        where: dict = {}
        if country_filter:
            where["country"] = {"contains": country_filter}
        if must_export_to_eu:
            where["exporting_to_eu"] = True
        # Filter by VERIFIED status using raw query since status is an enum
        # We use a list to filter where status equals VERIFIED string value

        all_suppliers = await prisma.supplier.find_many(
            where=where,
        )

        # Filter by status == VERIFIED
        verified_suppliers = [
            s for s in all_suppliers
            if (hasattr(s.status, 'value') and s.status.value == "VERIFIED") or str(s.status) == "VERIFIED"
        ]

        matches = []
        for supplier in verified_suppliers:
            score, reasons = self._calculate_match_score(
                supplier=supplier,
                required_industry=required_industry,
                required_categories=required_categories or [],
                required_certifications=required_certifications or [],
            )

            if score >= min_score:
                certs = supplier.certifications if isinstance(supplier.certifications, list) else []
                matches.append(SupplierMatchResult(
                    supplier_id=supplier.id,
                    company_name=supplier.company_name,
                    country=supplier.country,
                    industry=supplier.industry,
                    match_score=score,
                    match_reasons=reasons,
                    certifications=certs,
                    production_capacity=supplier.production_capacity,
                    exporting_to_eu=supplier.exporting_to_eu,
                ))

        matches.sort(key=lambda x: x.match_score, reverse=True)
        logger.info(
            f"Found {len(matches)} matching suppliers for industry='{required_industry}'",
        )
        return matches

    def _calculate_match_score(
        self,
        supplier,
        required_industry: str,
        required_categories: list[str],
        required_certifications: list[str],
    ) -> tuple[float, list[str]]:
        """
        Calculate match score between supplier and RFQ requirements.

        Score components (0-1 each):
        - Industry match: 0.4 weight
        - Category match: 0.25 weight
        - Certification match: 0.2 weight
        - EU export status: 0.15 weight (if required)

        Returns:
            Tuple of (score, list of match reasons)
        """
        score = 0.0
        reasons = []

        industry_weight = 0.4
        category_weight = 0.25
        cert_weight = 0.2
        eu_export_weight = 0.15

        supplier_industry_lower = supplier.industry.lower()
        required_industry_lower = required_industry.lower()

        if required_industry_lower in supplier_industry_lower:
            score += industry_weight
            reasons.append(f"Industry match: {supplier.industry}")
        elif any(cat.lower() in supplier_industry_lower for cat in required_categories):
            score += industry_weight * 0.7
            reasons.append(f"Related industry: {supplier.industry}")

        if required_categories:
            category_matches = sum(
                1 for cat in required_categories
                if cat.lower() in supplier_industry_lower
            )
            if category_matches > 0:
                cat_score = min(category_matches / len(required_categories), 1.0) * category_weight
                score += cat_score
                reasons.append(f"Category match: {category_matches}/{len(required_categories)} categories")

        certs = supplier.certifications if isinstance(supplier.certifications, list) else []
        if required_certifications and certs:
            cert_matches = [
                cert for cert in required_certifications
                if any(cert.upper() in c.upper() or c.upper() in cert.upper() for c in certs)
            ]
            if cert_matches:
                cert_score = min(len(cert_matches) / len(required_certifications), 1.0) * cert_weight
                score += cert_score
                reasons.append(f"Certifications: {', '.join(cert_matches)}")

        if supplier.exporting_to_eu:
            score += eu_export_weight
            reasons.append("Already exporting to EU")

        return round(score, 2), reasons

    async def get_top_suppliers_for_rfq(
        self,
        rfq_industry: str,
        rfq_categories: list[str] | None = None,
        rfq_countries: list[str] | None = None,
        top_n: int = 10,
    ) -> list[SupplierMatchResult]:
        """
        Get top N suppliers for an RFQ, with multi-country support.

        Args:
            rfq_industry: Industry for the RFQ
            rfq_categories: Product categories needed
            rfq_countries: Preferred countries (EU + Turkey by default)
            top_n: Number of top suppliers to return

        Returns:
            Top N matching suppliers
        """
        all_matches = []

        countries_to_check = rfq_countries or ["Turkey", "Germany", "Italy", "Spain", "Poland", "France"]

        for country in countries_to_check:
            matches = await self.find_matching_suppliers(
                required_industry=rfq_industry,
                required_categories=rfq_categories,
                country_filter=country,
                must_export_to_eu=True,
            )
            all_matches.extend(matches)

        deduped = {m.supplier_id: m for m in all_matches}
        unique_matches = list(deduped.values())
        unique_matches.sort(key=lambda x: x.match_score, reverse=True)

        return unique_matches[:top_n]

    async def record_match_event(
        self,
        supplier_id: int,
        rfq_industry: str,
        match_score: float,
        event_type: str = "rfq_matched",
    ) -> None:
        """
        Record a supplier match event for analytics.

        Args:
            supplier_id: ID of matched supplier
            rfq_industry: Industry of the RFQ
            match_score: Calculated match score
            event_type: Type of match event
        """
        supplier = await prisma.supplier.find_unique(where={"id": supplier_id})
        if not supplier:
            logger.warning(f"Supplier not found: {supplier_id}")
            return

        extra_data = supplier.extra_data or {} if isinstance(supplier.extra_data, dict) else {}

        match_history = extra_data.get("match_history", [])
        match_history.append({
            "rfq_industry": rfq_industry,
            "match_score": match_score,
            "event_type": event_type,
        })
        extra_data["match_history"] = match_history[-50:]

        await prisma.supplier.update(
            where={"id": supplier_id},
            data={"extra_data": json.dumps(extra_data)},
        )

        await prisma.auditlog.create(
            data={
                "action": "supplier_matched",
                "entity_type": "supplier",
                "entity_id": supplier_id,
                "details": json.dumps({
                    "rfq_industry": rfq_industry,
                    "match_score": match_score,
                    "event_type": event_type,
                }),
            }
        )
        logger.info(
            f"Recorded match event for supplier {supplier_id}",
        )


async def get_supplier_matching_service() -> SupplierMatchingService:
    return SupplierMatchingService()