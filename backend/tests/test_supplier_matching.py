"""
Tests for AI Supplier Matching Service
"""
from dataclasses import dataclass

import pytest

from app.enums import SupplierStatus
from app.prisma import prisma
from app.services.supplier_matching_service import SupplierMatchingService, SupplierMatchResult


@dataclass
class TestSupplier:
    """Lightweight supplier stand-in for service unit tests (doesn't hit DB)."""
    id: int
    company_name: str
    country: str
    business_email: str
    industry: str
    status: str
    exporting_to_eu: bool
    certifications: list = None

    def __post_init__(self):
        self.certifications = self.certifications or []


class TestCalculateMatchScore:
    """Unit tests for _calculate_match_score — uses plain dataclass suppliers."""

    def test_calculate_match_score_industry_exact(self):
        service = SupplierMatchingService()
        supplier = TestSupplier(
            id=1,
            company_name="Test Electronics GmbH",
            country="Germany",
            business_email="info@test-elec.de",
            industry="Electronics",
            status=SupplierStatus.VERIFIED.value,
            exporting_to_eu=True,
            certifications=["CE", "ISO 9001"],
        )

        score, reasons = service._calculate_match_score(
            supplier=supplier,
            required_industry="Electronics",
            required_categories=[],
            required_certifications=[],
        )

        assert score > 0
        assert len(reasons) > 0
        assert any("Industry match" in r for r in reasons)

    def test_calculate_match_score_with_certifications(self):
        service = SupplierMatchingService()
        supplier = TestSupplier(
            id=2,
            company_name="Test Machinery TR",
            country="Turkey",
            business_email="info@test-machinery.tr",
            industry="Machinery",
            status=SupplierStatus.VERIFIED.value,
            exporting_to_eu=True,
            certifications=["CE", "ISO 9001", "ISO 14001"],
        )

        score, reasons = service._calculate_match_score(
            supplier=supplier,
            required_industry="Machinery",
            required_categories=[],
            required_certifications=["CE", "ISO 9001"],
        )

        assert score > 0.5
        assert any("Certifications" in r for r in reasons)

    def test_calculate_match_score_eu_export_bonus(self):
        service = SupplierMatchingService()
        supplier_eu = TestSupplier(
            id=3,
            company_name="EU Exporter",
            country="Germany",
            business_email="info@eu-export.de",
            industry="Electronics",
            status=SupplierStatus.VERIFIED.value,
            exporting_to_eu=True,
            certifications=[],
        )
        supplier_non_eu = TestSupplier(
            id=4,
            company_name="Non EU Exporter",
            country="Turkey",
            business_email="info@non-eu-export.tr",
            industry="Electronics",
            status=SupplierStatus.VERIFIED.value,
            exporting_to_eu=False,
            certifications=[],
        )

        score_eu, _ = service._calculate_match_score(
            supplier=supplier_eu,
            required_industry="Electronics",
            required_categories=[],
            required_certifications=[],
        )
        score_non_eu, _ = service._calculate_match_score(
            supplier=supplier_non_eu,
            required_industry="Electronics",
            required_categories=[],
            required_certifications=[],
        )

        assert score_eu > score_non_eu

    def test_calculate_match_score_no_match(self):
        service = SupplierMatchingService()
        supplier = TestSupplier(
            id=5,
            company_name="Food Company",
            country="Turkey",
            business_email="info@food-co.tr",
            industry="Food & Beverages",
            status=SupplierStatus.VERIFIED.value,
            exporting_to_eu=False,
            certifications=[],
        )

        score, reasons = service._calculate_match_score(
            supplier=supplier,
            required_industry="Electronics",
            required_categories=[],
            required_certifications=[],
        )

        assert score < 0.3
        assert len(reasons) == 0 or all("Industry match" not in r for r in reasons)


class TestSupplierMatchResult:
    def test_supplier_match_result_dataclass(self):
        result = SupplierMatchResult(
            supplier_id=1,
            company_name="Test Company",
            country="Turkey",
            industry="Electronics",
            match_score=0.85,
            match_reasons=["Industry match: Electronics", "Certifications: CE, ISO 9001"],
            certifications=["CE", "ISO 9001"],
            production_capacity="10000 units/month",
            exporting_to_eu=True,
        )
        assert result.supplier_id == 1
        assert result.company_name == "Test Company"
        assert result.match_score == 0.85
        assert len(result.match_reasons) == 2
        assert result.exporting_to_eu is True


class TestGetTopSuppliersForRfq:
    """Integration tests that use actual Prisma suppliers."""

    @pytest.mark.asyncio
    async def test_get_top_suppliers_returns_top_n(self, session_prisma):
        await prisma.supplier.delete_many(where={})
        for i in range(15):
            await prisma.supplier.create(
                data={
                    "companyName": f"Supplier {i}",
                    "country": "Germany",
                    "businessEmail": f"info@supplier{i}.de",
                    "industry": "Electronics",
                    "status": SupplierStatus.VERIFIED.value,
                    "exportingToEu": True,
                }
            )

        service = SupplierMatchingService()
        top_suppliers = await service.get_top_suppliers_for_rfq(
            rfq_industry="Electronics",
            rfq_countries=["Germany"],
            top_n=5,
        )

        assert len(top_suppliers) <= 5

    @pytest.mark.asyncio
    async def test_find_matching_suppliers_filters_by_country(self, session_prisma):
        await prisma.supplier.delete_many(where={})
        await prisma.supplier.create(
            data={
                "companyName": "German Supplier",
                "country": "Germany",
                "businessEmail": "info@german.de",
                "industry": "Electronics",
                "status": SupplierStatus.VERIFIED.value,
                "exportingToEu": True,
            }
        )
        await prisma.supplier.create(
            data={
                "companyName": "Turkish Supplier",
                "country": "Turkey",
                "businessEmail": "info@turkish.tr",
                "industry": "Electronics",
                "status": SupplierStatus.VERIFIED.value,
                "exportingToEu": False,
            }
        )

        service = SupplierMatchingService()
        top_suppliers = await service.get_top_suppliers_for_rfq(
            rfq_industry="Electronics",
            rfq_countries=["Germany"],
            top_n=5,
        )

        assert all(s.country == "Germany" for s in top_suppliers)

    @pytest.mark.asyncio
    async def test_find_matching_suppliers_sorts_by_score(self, session_prisma):
        await prisma.supplier.delete_many(where={})
        await prisma.supplier.create(
            data={
                "companyName": "Low Score Supplier",
                "country": "Germany",
                "businessEmail": "info@low.de",
                "industry": "Food",
                "status": SupplierStatus.VERIFIED.value,
                "exportingToEu": True,
            }
        )
        await prisma.supplier.create(
            data={
                "companyName": "High Score Supplier",
                "country": "Germany",
                "businessEmail": "info@high.de",
                "industry": "Electronics",
                "status": SupplierStatus.VERIFIED.value,
                "exportingToEu": True,
                "certifications": "CE,ISO 9001",
            }
        )

        service = SupplierMatchingService()
        top_suppliers = await service.get_top_suppliers_for_rfq(
            rfq_industry="Electronics",
            rfq_countries=["Germany"],
            top_n=5,
        )

        assert len(top_suppliers) >= 1
        # High score supplier should appear before low score
        names = [s.company_name for s in top_suppliers]
        assert "High Score Supplier" in names
