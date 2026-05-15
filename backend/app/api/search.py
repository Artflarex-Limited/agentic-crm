"""
Semantic Search API endpoints.
POST /api/search/semantic - Semantic search with embeddings
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
    Semantic search using vector embeddings.

    - **query**: Text query to search
    - **index**: Target index ('leads', 'contacts', 'companies')
    - **embedding**: Pre-computed vector embedding (optional - will use ML service if not provided)
    - **use_semantic**: Whether to use semantic search (True) or keyword only (False)
    - **size**: Number of results to return
    - **filters**: Optional filters (stage, source, tags, etc.)
    """
    service = await get_search_service()

    embedding = request.embedding

    if embedding is None and request.use_semantic:
        embedding = await service.get_query_embedding(request.query)

    result = await service.semantic_search(
        index=request.index,
        query_text=request.query,
        embedding=embedding,
        size=request.size,
        filters=request.filters,
    )

    if embedding and request.use_semantic:
        result = await service.rerank_results(result, request.query)

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
    Semantic search for leads.

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
    Semantic search for contacts.

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
    Semantic search for companies.

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
    """Check semantic search service health."""
    service = await get_search_service()
    return await service.health_check()
