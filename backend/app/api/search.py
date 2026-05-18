"""
Search API endpoints.
POST /api/search/semantic - Semantic search (fallback to basic search since ES removed)
POST /api/search/leads
POST /api/search/contacts
POST /api/search/companies
"""
import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.search_service import get_search_service

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


class SemanticSearchRequest(BaseModel):
    query: str
    index: str = "leads"
    embedding: list[float] | None = None
    use_semantic: bool = True
    size: int = 10
    filters: dict | None = None


@router.post("/semantic")
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search — falls back to basic SQLite search since Elasticsearch is removed.

    - **query**: Text query to search
    - **index**: Target index ('leads', 'contacts', 'companies')
    - **embedding**: Pre-computed vector embedding (ignored — ES removed)
    - **use_semantic**: Ignored — ES removed
    - **size**: Number of results to return
    - **filters**: Optional filters (stage, source, tags, etc.)
    """
    service = await get_search_service()

    result = await service.semantic_search(
        index=request.index,
        query_text=request.query,
        embedding=request.embedding,
        size=request.size,
        filters=request.filters,
    )

    return result


@router.post("/leads")
async def search_leads(
    query: str,
    stage: str | None = None,
    source: str | None = None,
    tags: str | None = None,
    size: int = Query(default=10, ge=1, le=100),
):
    """
    Search for leads using SQLite full-text (Prisma contains).

    - **query**: Text query for search
    - **stage**: Filter by lead stage (new, contacted, qualified, etc.)
    - **source**: Filter by lead source (linkedin, email, web, etc.)
    - **tags**: Filter by tags (comma-separated)
    - **size**: Number of results (default 10, max 100)
    """
    service = await get_search_service()

    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",")]

    result = await service.search_leads(
        query=query,
        stage=stage,
        source=source,
        tags=tags_list,
        size=size,
    )

    return result


@router.post("/contacts")
async def search_contacts(
    query: str,
    company: str | None = None,
    title: str | None = None,
    size: int = Query(default=10, ge=1, le=100),
):
    """
    Search for contacts using SQLite full-text (Prisma contains).

    - **query**: Text query for search
    - **company**: Filter by company name
    - **title**: Filter by job title
    - **size**: Number of results (default 10, max 100)
    """
    service = await get_search_service()

    result = await service.search_contacts(
        query=query,
        company=company,
        title=title,
        size=size,
    )

    return result


@router.post("/companies")
async def search_companies(
    query: str,
    industry: str | None = None,
    size: str | None = None,
    size_limit: int = Query(default=10, ge=1, le=100),
):
    """
    Search for companies using SQLite full-text (Prisma contains).

    - **query**: Text query for search
    - **industry**: Filter by industry
    - **size**: Filter by company size range
    - **size_limit**: Number of results (default 10, max 100)
    """
    service = await get_search_service()

    result = await service.search_companies(
        query=query,
        industry=industry,
        size=size,
        size_limit=size_limit,
    )

    return result


@router.get("/health")
async def search_health():
    """Check search service health."""
    service = await get_search_service()
    return await service.health_check()
