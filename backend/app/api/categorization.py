"""
AI Product Categorization API endpoints.
POST /api/ai/categorize
"""
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.categorization_service import CategorizationService, get_categorization_service

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


class CategorizeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Product text description")
    name: Optional[str] = Field(None, description="Product name")


class CategorizeResponse(BaseModel):
    family: str
    cls: str
    commodity: str
    confidence: float
    tags: list[str]
    source: str


class CategorizeBatchRequest(BaseModel):
    texts: list[str] = Field(..., max_length=100, description="List of product texts")


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize_product(
    text: Optional[str] = None,
    image: Optional[UploadFile] = File(None),
):
    """
    Categorize a product using AI (image + NLP).

    - **text**: Product text description (name, description, etc.)
    - **image**: Optional product image for visual classification
    """
    service = await get_categorization_service()

    image_bytes = None
    if image:
        contents = await image.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        image_bytes = contents

    result = await service.categorize(text=text or "", image_bytes=image_bytes)

    return CategorizeResponse(
        family=result.family,
        cls=result.cls,
        commodity=result.commodity,
        confidence=result.confidence,
        tags=result.tags,
        source=result.source,
    )


@router.post("/categorize/batch", response_model=list[CategorizeResponse])
async def categorize_products_batch(request: CategorizeBatchRequest):
    """
    Batch categorize multiple products.
    """
    service = await get_categorization_service()
    results = []

    for text in request.texts:
        result = await service.categorize_from_text(text)
        results.append(
            CategorizeResponse(
                family=result.family,
                cls=result.cls,
                commodity=result.commodity,
                confidence=result.confidence,
                tags=result.tags,
                source=result.source,
            )
        )

    return results


@router.get("/categorize/taxonomy")
async def get_taxonomy():
    """
    Returns the 3-level category taxonomy.
    Family → Class → Commodity
    """
    from app.services.categorization_service import TAXONOMY_RULES

    taxonomy = []
    for rule in TAXONOMY_RULES:
        family = rule["family"][0].title() if rule["family"] else "Unknown"
        classes = []
        for cls_name, cls_keywords in rule["cls"].items():
            commodities = [
                c for c, c_kws in rule["commodity"].items() if any(kw in c.lower() for kw in cls_keywords)
            ]
            classes.append({"name": cls_name, "commodities": commodities})
        taxonomy.append({"family": family, "classes": classes})

    return {"taxonomy": taxonomy}