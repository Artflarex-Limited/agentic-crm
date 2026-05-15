"""
Tests for AI Product Categorization Service
"""
import pytest
from app.services.categorization_service import (
    CategorizationService,
    CategorizationResult,
    MACHINERY_KEYWORDS,
    TEXTILE_KEYWORDS,
    CHEMICAL_KEYWORDS,
)


class TestCategorizationService:
    @pytest.mark.asyncio
    async def test_categorize_machinery_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text(
            "Industrial machinery CNC milling machine for metalworking, high precision"
        )
        assert result.family == "Machinery"
        assert result.cls == "cnc"
        assert result.commodity == "cnc milling machine"
        assert result.confidence == 0.85
        assert result.source == "nlp_pipeline"

    @pytest.mark.asyncio
    async def test_categorize_pump_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text(
            "Industrial machinery centrifugal pump for water supply"
        )
        assert result.family == "Machinery"
        assert result.cls == "pump"
        assert result.commodity == "industrial pump"

    @pytest.mark.asyncio
    async def test_categorize_textile_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text(
            "Textile cotton woven fabric for garment manufacturing"
        )
        assert result.family == "Textile"
        assert result.cls == "woven"
        assert result.commodity == "cotton fabric"

    @pytest.mark.asyncio
    async def test_categorize_chemical_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text(
            "Chemical industrial solvent for cleaning and degreasing"
        )
        assert result.family == "Chemical"
        assert result.cls == "solvent"
        assert result.commodity == "industrial solvent"

    @pytest.mark.asyncio
    async def test_categorize_metal_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text(
            "Metal stainless steel plate for construction"
        )
        assert result.family == "Metal"
        assert result.cls == "steel"
        assert result.commodity == "steel plate"

    @pytest.mark.asyncio
    async def test_categorize_electronics_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text(
            "Electronics industrial sensor for temperature monitoring"
        )
        assert result.family == "Electronics"
        assert result.cls == "sensor"
        assert result.commodity == "industrial sensor"

    @pytest.mark.asyncio
    async def test_categorize_empty_text(self):
        service = CategorizationService()
        result = await service.categorize_from_text("")
        assert result.family in ("uncategorized", "unknown")
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_categorize_unknown_product(self):
        service = CategorizationService()
        result = await service.categorize_from_text("Random unknown product xyz")
        assert result.family in ["uncategorized", "unknown"]
        assert result.confidence <= 0.5

    @pytest.mark.asyncio
    async def test_extract_tags(self):
        service = CategorizationService()
        tags = service._extract_tags(
            "Industrial CNC milling machine with steel components"
        )
        assert isinstance(tags, list)
        assert len(tags) <= 20

    @pytest.mark.asyncio
    async def test_enrich_product_with_categories(self):
        service = CategorizationService()
        product = {
            "name": "CNC Milling Machine",
            "description": "Industrial CNC milling machine for metalworking",
        }
        enriched = await service.enrich_product_with_categories(product)
        assert "category_family" in enriched
        assert "category_class" in enriched
        assert "category_commodity" in enriched
        assert "category_confidence" in enriched
        assert "category_tags" in enriched
        assert enriched["category_family"] == "Machinery"


class TestTaxonomyKeywords:
    def test_machinery_keywords_structure(self):
        assert "family" in MACHINERY_KEYWORDS
        assert "cls" in MACHINERY_KEYWORDS
        assert "commodity" in MACHINERY_KEYWORDS
        assert MACHINERY_KEYWORDS["family"][0] == "machinery"

    def test_textile_keywords_structure(self):
        assert "family" in TEXTILE_KEYWORDS
        assert TEXTILE_KEYWORDS["family"][0] == "textile"

    def test_chemical_keywords_structure(self):
        assert "family" in CHEMICAL_KEYWORDS
        assert CHEMICAL_KEYWORDS["family"][0] == "chemical"

    def test_cnc_commodities_defined(self):
        cnc_keywords = MACHINERY_KEYWORDS["cls"]["cnc"]
        assert len(cnc_keywords) > 0
        assert any("cnc" in kw.lower() for kw in cnc_keywords)


class TestCategorizationResult:
    def test_categorization_result_dataclass(self):
        result = CategorizationResult(
            family="Machinery",
            cls="cnc",
            commodity="CNC Milling Machine",
            confidence=0.85,
            tags=["cnc", "milling", "machine"],
            source="nlp_pipeline",
        )
        assert result.family == "Machinery"
        assert result.cls == "cnc"
        assert result.commodity == "CNC Milling Machine"
        assert result.confidence == 0.85
        assert len(result.tags) == 3
        assert result.source == "nlp_pipeline"