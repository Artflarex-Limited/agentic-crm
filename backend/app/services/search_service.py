"""
Search Service - Prisma-backed simple search.
Elasticsearch-based semantic search has been removed per the migration plan.
This module provides basic SQLite LIKE-based search via Prisma contains filters.
"""
import logging
from typing import Any

from app.prisma import prisma

logger = logging.getLogger(__name__)


class SearchService:
    """Simple search service using Prisma contains filters."""

    async def health_check(self) -> dict[str, Any]:
        """Check search service health."""
        try:
            await prisma.$connect()
            return {"status": "healthy", "provider": "prisma-sqlite"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def search_leads(
        self,
        query: str,
        stage: str | None = None,
        source: str | None = None,
        tags: list[str] | None = None,
        size: int = 10,
    ) -> dict[str, Any]:
        """Search leads by text query with optional filters using Prisma contains."""
        where: dict[str, Any] = {}

        if query:
            # Use OR across multiple text fields
            where["OR"] = [
                {"notes": {"contains": query}},
                {"contact": {"is": {"OR": [
                    {"first_name": {"contains": query}},
                    {"last_name": {"contains": query}},
                    {"email": {"contains": query}},
                ]}}},
            ]

        if stage:
            where["stage"] = stage
        if source:
            where["source"] = source
        if tags:
            # Prisma doesn't have array contains for JSON, so we do client-side filtering
            pass

        try:
            leads = await prisma.lead.find_many(
                where=where,
                include={"contact": True, "assigned_agent": True},
                take=size,
                order={"created_at": "desc"},
            )

            results = []
            for lead in leads:
                # Client-side tag filtering
                if tags:
                    lead_tags = lead.tags or []
                    if not any(t in lead_tags for t in tags):
                        continue

                stage_val = lead.stage.value if hasattr(lead.stage, 'value') else str(lead.stage)
                source_val = lead.source.value if hasattr(lead.source, 'value') else str(lead.source)
                contact_name = ""
                contact_email = ""
                if lead.contact:
                    contact_name = f"{lead.contact.first_name or ''} {lead.contact.last_name or ''}".strip()
                    contact_email = lead.contact.email or ""

                results.append({
                    "id": lead.id,
                    "stage": stage_val,
                    "source": source_val,
                    "score": lead.score,
                    "tags": lead.tags or [],
                    "notes": lead.notes,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "created_at": lead.created_at.isoformat() if lead.created_at else None,
                })

            return {"total": len(results), "results": results}

        except Exception as e:
            logger.error(f"Lead search error: {e}")
            return {"total": 0, "results": [], "error": str(e)}

    async def search_contacts(
        self,
        query: str,
        company: str | None = None,
        title: str | None = None,
        size: int = 10,
    ) -> dict[str, Any]:
        """Search contacts using Prisma contains."""
        where: dict[str, Any] = {}

        if query:
            where["OR"] = [
                {"first_name": {"contains": query}},
                {"last_name": {"contains": query}},
                {"email": {"contains": query}},
                {"title": {"contains": query}},
            ]

        if company:
            where["company"] = {"is": {"name": {"contains": company}}}
        if title:
            where["title"] = {"contains": title}

        try:
            contacts = await prisma.contact.find_many(
                where=where,
                include={"company": True},
                take=size,
                order={"created_at": "desc"},
            )

            results = []
            for contact in contacts:
                name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                results.append({
                    "id": contact.id,
                    "name": name,
                    "email": contact.email,
                    "title": contact.title,
                    "phone": contact.phone,
                    "company_name": contact.company.name if contact.company else None,
                    "linkedin_url": contact.linkedin_url,
                    "created_at": contact.created_at.isoformat() if contact.created_at else None,
                })

            return {"total": len(results), "results": results}

        except Exception as e:
            logger.error(f"Contact search error: {e}")
            return {"total": 0, "results": [], "error": str(e)}

    async def search_companies(
        self,
        query: str,
        industry: str | None = None,
        size: str | None = None,
        size_limit: int = 10,
    ) -> dict[str, Any]:
        """Search companies using Prisma contains."""
        where: dict[str, Any] = {}

        if query:
            where["OR"] = [
                {"name": {"contains": query}},
                {"domain": {"contains": query}},
                {"industry": {"contains": query}},
            ]

        if industry:
            where["industry"] = {"contains": industry}

        try:
            companies = await prisma.company.find_many(
                where=where,
                take=size_limit,
                order={"created_at": "desc"},
            )

            results = []
            for company in companies:
                results.append({
                    "id": company.id,
                    "name": company.name,
                    "domain": company.domain,
                    "industry": company.industry,
                    "size": company.size,
                    "linkedin_url": company.linkedin_url,
                    "created_at": company.created_at.isoformat() if company.created_at else None,
                })

            return {"total": len(results), "results": results}

        except Exception as e:
            logger.error(f"Company search error: {e}")
            return {"total": 0, "results": [], "error": str(e)}

    # Semantic search stubs — ES removed; these return empty results
    async def semantic_search(
        self,
        index: str,
        query_text: str,
        embedding: list[float] | None = None,
        size: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Semantic search placeholder — ES removed. Falls back to basic search."""
        logger.info(f"Semantic search called but ES is removed; using basic search for index={index}")
        if index == "leads":
            return await self.search_leads(query=query_text, size=size)
        elif index == "contacts":
            return await self.search_contacts(query=query_text, size=size)
        elif index == "companies":
            return await self.search_companies(query=query_text, size_limit=size)
        return {"total": 0, "results": []}

    async def get_query_embedding(self, query: str) -> list[float] | None:
        """ML embedding service removed — no-op."""
        return None

    async def rerank_results(self, results: dict[str, Any], query: str) -> dict[str, Any]:
        """Reranking not available without ES — return as-is."""
        return results

    async def ensure_indices(self) -> None:
        """No-op — SQLite has no indices to create."""
        pass

    async def index_lead(self, lead_id: int, data: dict[str, Any], embedding: list[float] | None = None) -> dict[str, Any]:
        """No-op — search is now DB-backed, no manual indexing needed."""
        return {}

    async def index_contact(self, contact_id: int, data: dict[str, Any], embedding: list[float] | None = None) -> dict[str, Any]:
        return {}

    async def index_company(self, company_id: int, data: dict[str, Any], embedding: list[float] | None = None) -> dict[str, Any]:
        return {}

    async def delete_document(self, index: str, doc_id: str) -> dict[str, Any]:
        return {}


_search_service: SearchService | None = None


async def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service