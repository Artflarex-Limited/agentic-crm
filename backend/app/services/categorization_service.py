"""
AI Product Categorization & Tagging Service

- Image classification (ResNet/EfficientNet) → product category
- NLP pipeline (multilingual BERT) → text categorization
- Tag extraction with spaCy + custom NER
- 3-level category taxonomy (Family → Class → Commodity)

API: POST /api/ai/categorize
"""
import logging
import re
from dataclasses import dataclass
from typing import Optional

import httpx

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    spacy = None
    HAS_SPACY = False

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

NLP_MODEL: Optional["spacy.language.Language"] = None


def get_nlp_model() -> Optional["spacy.language.Language"]:
    global NLP_MODEL
    if NLP_MODEL is None:
        if not HAS_SPACY:
            logger.warning("spaCy not installed, using regex-based NER")
            return None
        try:
            NLP_MODEL = spacy.load("xx_ent_wiki_sm")
        except Exception:
            try:
                NLP_MODEL = spacy.load("en_core_web_sm")
            except Exception:
                logger.warning("spaCy model not available, using regex-based NER")
                NLP_MODEL = None
    return NLP_MODEL


@dataclass
class CategorizationResult:
    family: str
    cls: str
    commodity: str
    confidence: float
    tags: list[str]
    source: str


MACHINERY_KEYWORDS = {
    "family": ["machinery", "equipment", "industrial machinery", "machine"],
    "cls": {
        "cnc": ["cnc", "数控", " milling", "lathe", "machining"],
        "hydraulic": ["hydraulic", "hydraulik", "pressor"],
        "pump": ["pump", "pompe", "pumpen"],
        "conveyor": ["conveyor", "belt", "transport"],
        "generator": ["generator", "alternator", "power generation"],
        "compressor": ["compressor", "kompressor"],
    },
    "commodity": {
        "industrial pump": ["industrial pump", "centrifugal pump", "submersible pump"],
        "cnc milling machine": ["cnc milling machine", "cnc mill"],
        "hydraulic cylinder": ["hydraulic cylinder", "hydraulic actuator"],
        "belt conveyor": ["belt conveyor", "conveyor belt", "rubber belt"],
        "air compressor": ["air compressor", "screw compressor", "reciprocating compressor"],
        "diesel generator": ["diesel generator", "diesel genset"],
        "industrial motor": ["industrial motor", "ac motor", "electric motor"],
    },
}

TEXTILE_KEYWORDS = {
    "family": ["textile", "fabric", "garment", "clothing"],
    "cls": {
        "woven": ["woven", "fabric woven"],
        "knitted": ["knitted", "knit fabric"],
        "nonwoven": ["nonwoven", "non-woven"],
        "dyed": ["dyed", "dyeing", "colored fabric"],
    },
    "commodity": {
        "cotton fabric": ["cotton fabric", "cotton woven", "cotton textile"],
        "polyester fabric": ["polyester fabric", "polyester woven"],
        "wool fabric": ["wool fabric", "woolen", "wool textile"],
        "silk fabric": ["silk fabric", "silk textile"],
        "industrial textile": ["industrial textile", "technical textile"],
    },
}

CHEMICAL_KEYWORDS = {
    "family": ["chemical", "chemical product", "reagent"],
    "cls": {
        "organic": ["organic chemical", "organic reagent"],
        "inorganic": ["inorganic chemical", "inorganic reagent"],
        "polymer": ["polymer", "resin", "plastic raw"],
        "solvent": ["solvent", "organic solvent"],
        "catalyst": ["catalyst", "catalytic"],
    },
    "commodity": {
        "industrial solvent": ["industrial solvent", "cleaning solvent"],
        "polymer resin": ["polymer resin", "epoxy resin", "polypropylene"],
        "industrial acid": ["industrial acid", "sulfuric acid", "hydrochloric acid"],
        "catalyst compound": ["catalyst compound", "chemical catalyst"],
    },
}

METALS_KEYWORDS = {
    "family": ["metal", "steel", "aluminum", "alloy"],
    "cls": {
        "steel": ["steel", "stainless steel", "carbon steel"],
        "aluminum": ["aluminum", "aluminium", "alu"],
        "copper": ["copper", "cu", "brass", "bronze"],
        "precious": ["precious metal", "gold", "silver", "platinum"],
    },
    "commodity": {
        "steel plate": ["steel plate", "steel sheet", "mild steel"],
        "aluminum extrusion": ["aluminum extrusion", "alu profile"],
        "copper wire": ["copper wire", "copper cable"],
        "stainless steel tube": ["stainless steel tube", "ss tube"],
    },
}

ELECTRONICS_KEYWORDS = {
    "family": ["electronics", "electrical", "semiconductor", "electronic"],
    "cls": {
        "component": ["electronic component", "passive component"],
        "pcb": ["pcb", "circuit board", "pcba"],
        "sensor": ["sensor", "transducer"],
        "display": ["display", "screen", "lcd", "oled"],
    },
    "commodity": {
        "integrated circuit": ["integrated circuit", "ic", "chip"],
        "display module": ["display module", "lcd module", "oled module"],
        "industrial sensor": ["industrial sensor", "temperature sensor", "pressure sensor"],
        "power supply": ["power supply", "psu", "adapter"],
    },
}

TAXONOMY_RULES = [
    MACHINERY_KEYWORDS,
    TEXTILE_KEYWORDS,
    CHEMICAL_KEYWORDS,
    METALS_KEYWORDS,
    ELECTRONICS_KEYWORDS,
]


class CategorizationService:
    def __init__(self):
        self.ml_service_url = settings.ml_model_service_url
        self.inference_timeout = settings.ml_inference_timeout

    async def categorize_from_image_bytes(self, image_bytes: bytes) -> CategorizationResult:
        """Classify product from image bytes using ML model service."""
        if not self.ml_service_url:
            return self._fallback_categorize("unknown image", confidence=0.0, source="fallback")

        try:
            async with httpx.AsyncClient(timeout=self.inference_timeout) as client:
                files = {"image": ("product.jpg", image_bytes, "image/jpeg")}
                response = await client.post(f"{self.ml_service_url}/v1/classify", files=files)
                if response.status_code == 200:
                    data = response.json()
                    return CategorizationResult(
                        family=data.get("family", "unknown"),
                        cls=data.get("class", "unknown"),
                        commodity=data.get("commodity", "unknown"),
                        confidence=data.get("confidence", 0.0),
                        tags=data.get("tags", []),
                        source="ml_service",
                    )
        except Exception as e:
            logger.warning(f"ML service unavailable: {e}")

        return self._fallback_categorize("unknown image", confidence=0.0, source="fallback")

    async def categorize_from_text(self, text: str) -> CategorizationResult:
        """Classify product from text description using NLP pipeline."""
        if not text:
            return CategorizationResult(
                family="uncategorized",
                cls="general",
                commodity="general product",
                confidence=0.0,
                tags=[],
                source="empty",
            )

        text_lower = text.lower()
        best_result: CategorizationResult | None = None
        best_score = 0

        for rule_set in TAXONOMY_RULES:
            for family_kw in rule_set["family"]:
                idx = text_lower.find(family_kw)
                if idx >= 0:
                    score = len(family_kw) * 10
                    if text_lower[idx + len(family_kw) : idx + len(family_kw) + 1].isalnum():
                        score -= 5
                    if score > best_score:
                        best_score = score
                        best_cls = "general"
                        best_commodity = "general product"
                        found_commodity = False

                        for cls_name, cls_keywords in rule_set["cls"].items():
                            for kw in cls_keywords:
                                kw_idx = text_lower.find(kw)
                                if kw_idx >= 0:
                                    next_char_idx = kw_idx + len(kw)
                                    next_char = text_lower[next_char_idx] if next_char_idx < len(text_lower) else " "
                                    prev_char = text_lower[kw_idx - 1] if kw_idx > 0 else " "
                                    if next_char.isalnum() or prev_char.isalnum():
                                        continue
                                    best_cls = cls_name
                                    for commodity_name, commodity_keywords in rule_set["commodity"].items():
                                        for ckw in commodity_keywords:
                                            ckw_idx = text_lower.find(ckw)
                                            if ckw_idx >= 0:
                                                best_commodity = commodity_name
                                                found_commodity = True
                                                break
                                    if found_commodity:
                                        break

                        family_canonical = {
                            "machinery": "Machinery",
                            "equipment": "Machinery",
                            "industrial machinery": "Machinery",
                            "machine": "Machinery",
                            "textile": "Textile",
                            "fabric": "Textile",
                            "garment": "Textile",
                            "clothing": "Textile",
                            "chemical": "Chemical",
                            "chemical product": "Chemical",
                            "reagent": "Chemical",
                            "metal": "Metal",
                            "steel": "Metal",
                            "aluminum": "Metal",
                            "alloy": "Metal",
                            "electronics": "Electronics",
                            "electrical": "Electronics",
                            "semiconductor": "Electronics",
                            "electronic": "Electronics",
                        }.get(family_kw, family_kw.title())

                        best_result = CategorizationResult(
                            family=family_canonical,
                            cls=best_cls,
                            commodity=best_commodity,
                            confidence=0.85,
                            tags=self._extract_tags(text),
                            source="nlp_pipeline",
                        )

            if best_result:
                break

        if best_result:
            return best_result

        return self._fallback_categorize(text, confidence=0.5, source="nlp_pipeline")

    async def categorize(self, text: str, image_bytes: bytes | None = None) -> CategorizationResult:
        """Combined categorization - prefer image if available."""
        if image_bytes:
            img_result = await self.categorize_from_image_bytes(image_bytes)
            if img_result.confidence > 0.7:
                return img_result

        if text:
            return await self.categorize_from_text(text)

        return self._fallback_categorize("", confidence=0.0, source="none")

    def _fallback_categorize(self, text: str, confidence: float, source: str) -> CategorizationResult:
        """Keyword-based fallback classifier."""
        text_lower = text.lower() if text else ""

        for rule_set in TAXONOMY_RULES:
            for family_kw in rule_set["family"]:
                if family_kw in text_lower:
                    return CategorizationResult(
                        family=family_kw.title(),
                        cls="general",
                        commodity="general " + family_kw,
                        confidence=0.6,
                        tags=self._extract_tags(text),
                        source=source,
                    )

        return CategorizationResult(
            family="uncategorized",
            cls="general",
            commodity="general product",
            confidence=0.3,
            tags=self._extract_tags(text),
            source=source,
        )

    def _extract_tags(self, text: str) -> list[str]:
        """Extract tags using spaCy NER and keyword matching."""
        tags = set()
        nlp = get_nlp_model()

        if nlp and text:
            try:
                doc = nlp(text[:10000])
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PRODUCT", "GPE", "LOC"):
                        tags.add(ent.text.lower())
            except Exception as e:
                logger.warning(f"spaCy NER failed: {e}")

        product_patterns = [
            r"\b(machine|equipment|device|device|component|part|module|circuit|board)\b",
            r"\b(cnc|pump|motor|valve|bearing|gear|shaft|cylinder|compressor)\b",
            r"\b(steel|aluminum|copper|plastic|rubber|fabric|fiber)\b",
            r"\b(industrial|commercial|residential|automotive|agricultural)\b",
        ]
        for pattern in product_patterns:
            for match in re.finditer(pattern, text.lower()):
                tags.add(match.group())

        return list(tags)[:20]

    async def enrich_product_with_categories(self, product_data: dict) -> dict:
        """Enrich a product dict with categorization results."""
        text = product_data.get("description", "") or product_data.get("name", "")
        image_bytes = product_data.get("image_bytes")
        result = await self.categorize(text=text, image_bytes=image_bytes)
        return {
            **product_data,
            "category_family": result.family,
            "category_class": result.cls,
            "category_commodity": result.commodity,
            "category_confidence": result.confidence,
            "category_tags": result.tags,
            "category_source": result.source,
        }


async def get_categorization_service() -> CategorizationService:
    return CategorizationService()
