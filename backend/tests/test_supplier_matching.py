"""
Tests for AI Supplier Matching Service
"""
import pytest

from app.models.models import Supplier, SupplierStatus
from app.services.supplier_matching_service import SupplierMatchingService, SupplierMatchResult


class TestSupplierMatchingService:
    @pytest.mark.asyncio
    async def test_calculate_match_score_industry_exact(self, db_session):
        service = SupplierMatchingService()
        supplier = Supplier(
            company_name="Test Electronics GmbH",
            country="Germany",
            business_email="info@test-elec.de",
            industry="Electronics",
            status=SupplierStatus.VERIFIED,
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

    @pytest.mark.asyncio
    async def test_calculate_match_score_with_certifications(self, db_session):
        service = SupplierMatchingService()
        supplier = Supplier(
            company_name="Test Machinery TR",
            country="Turkey",
            business_email="info@test-machinery.tr",
            industry="Machinery",
            status=SupplierStatus.VERIFIED,
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

    @pytest.mark.asyncio
    async def test_calculate_match_score_eu_export_bonus(self, db_session):
        service = SupplierMatchingService()
        supplier_eu = Supplier(
            company_name="EU Exporter",
            country="Germany",
            business_email="info@eu-export.de",
            industry="Electronics",
            status=SupplierStatus.VERIFIED,
            exporting_to_eu=True,
        )
        supplier_non_eu = Supplier(
            company_name="Non EU Exporter",
            country="Turkey",
            business_email="info@non-eu-export.tr",
            industry="Electronics",
            status=SupplierStatus.VERIFIED,
            exporting_to_eu=False,
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

    @pytest.mark.asyncio
    async def test_calculate_match_score_no_match(self, db_session):
        service = SupplierMatchingService()
        supplier = Supplier(
            company_name="Food Company",
            country="Turkey",
            business_email="info@food-co.tr",
            industry="Food & Beverages",
            status=SupplierStatus.VERIFIED,
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


class TestSupplierMatchingServiceFindMatches:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup - integration test")
    async def test_find_matching_suppliers_filters_by_country(self, db_session):
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup - integration test")
    async def test_find_matching_suppliers_filters_by_eu_export(self, db_session):
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup - integration test")
    async def test_find_matching_suppliers_sorts_by_score(self, db_session):
        pass


class TestGetTopSuppliersForRfq:
    @pytest.mark.asyncio
    async def test_get_top_suppliers_returns_top_n(self, db_session):
        service = SupplierMatchingService()
        for i in range(15):
            supplier = Supplier(
                company_name=f"Supplier {i}",
                country="Germany",
                business_email=f"info@supplier{i}.de",
                industry="Electronics",
                status=SupplierStatus.VERIFIED,
                exporting_to_eu=True,
            )
            db_session.add(supplier)
        await db_session.commit()

        top_suppliers = await service.get_top_suppliers_for_rfq(
            rfq_industry="Electronics",
            rfq_countries=["Germany"],
            top_n=5,
        )

        assert len(top_suppliers) <= 5


class TestRecordMatchEvent:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup - integration test")
    async def test_record_match_event_creates_audit_log(self, db_session):
        pass