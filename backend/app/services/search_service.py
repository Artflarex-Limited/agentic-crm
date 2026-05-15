"""
Semantic Search Service
Provides vector-based semantic search for leads, contacts, and companies.
Uses Elasticsearch with embedding models for similarity search.
"""
import logging
from typing import Any

from app.core.clients import es_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SearchService:
    LEAD_INDEX = "leads"
    CONTACT_INDEX = "contacts"
    COMPANY_INDEX = "companies"

    def __init__(self):
        self.es = es_client

    async def ensure_indices(self) -> None:
        """Create indices with vector search mappings if they don't exist."""
        index_mappings = {
            self.LEAD_INDEX: {
                "mappings": {
                    "properties": {
                        "lead_id": {"type": "integer"},
                        "contact_id": {"type": "integer"},
                        "email": {"type": "keyword"},
                        "name": {"type": "text"},
                        "title": {"type": "text"},
                        "company": {"type": "text"},
                        "notes": {"type": "text"},
                        "tags": {"type": "keyword"},
                        "stage": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "embedding": {"type": "dense_vector", "dims": 1536, "index": True, "similarity": "cosine"},
                    }
                }
            },
            self.CONTACT_INDEX: {
                "mappings": {
                    "properties": {
                        "contact_id": {"type": "integer"},
                        "email": {"type": "keyword"},
                        "first_name": {"type": "text"},
                        "last_name": {"type": "text"},
                        "title": {"type": "text"},
                        "company": {"type": "text"},
                        "phone": {"type": "keyword"},
                        "linkedin_url": {"type": "keyword"},
                        "embedding": {"type": "dense_vector", "dims": 1536, "index": True, "similarity": "cosine"},
                    }
                }
            },
            self.COMPANY_INDEX: {
                "mappings": {
                    "properties": {
                        "company_id": {"type": "integer"},
                        "name": {"type": "text"},
                        "domain": {"type": "keyword"},
                        "industry": {"type": "text"},
                        "size": {"type": "keyword"},
                        "linkedin_url": {"type": "keyword"},
                        "embedding": {"type": "dense_vector", "dims": 1536, "index": True, "similarity": "cosine"},
                    }
                }
            },
        }

        for index_name, _index_config in index_mappings.items():
            try:
                await self.es.search(
                    index=index_name,
                    query={"match_all": {}},
                    size=0,
                )
                logger.info(f"Index {index_name} exists")
            except Exception:
                logger.info(f"Creating index {index_name}")
                try:
                    await self.es.index(index=index_name, document={})
                    logger.info(f"Index {index_name} created")
                except Exception as e:
                    logger.warning(f"Could not create index {index_name}: {e}")

    async def index_lead(self, lead_id: int, data: dict[str, Any], embedding: list[float] | None = None) -> dict[str, Any]:
        """Index a lead for semantic search."""
        doc = {
            "lead_id": lead_id,
            "contact_id": data.get("contact_id"),
            "email": data.get("email"),
            "name": data.get("name", ""),
            "title": data.get("title", ""),
            "company": data.get("company", ""),
            "notes": data.get("notes", ""),
            "tags": data.get("tags", []),
            "stage": data.get("stage", ""),
            "source": data.get("source", ""),
        }
        if embedding:
            doc["embedding"] = embedding

        return await self.es.index(index=self.LEAD_INDEX, document=doc, id=str(lead_id))

    async def index_contact(self, contact_id: int, data: dict[str, Any], embedding: list[float] | None = None) -> dict[str, Any]:
        """Index a contact for semantic search."""
        doc = {
            "contact_id": contact_id,
            "email": data.get("email"),
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "title": data.get("title", ""),
            "company": data.get("company", ""),
            "phone": data.get("phone"),
            "linkedin_url": data.get("linkedin_url"),
        }
        if embedding:
            doc["embedding"] = embedding

        return await self.es.index(index=self.CONTACT_INDEX, document=doc, id=str(contact_id))

    async def index_company(self, company_id: int, data: dict[str, Any], embedding: list[float] | None = None) -> dict[str, Any]:
        """Index a company for semantic search."""
        doc = {
            "company_id": company_id,
            "name": data.get("name", ""),
            "domain": data.get("domain", ""),
            "industry": data.get("industry", ""),
            "size": data.get("size", ""),
            "linkedin_url": data.get("linkedin_url"),
        }
        if embedding:
            doc["embedding"] = embedding

        return await self.es.index(index=self.COMPANY_INDEX, document=doc, id=str(company_id))

    async def semantic_search(
        self,
        index: str,
        query_text: str,
        embedding: list[float] | None = None,
        size: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Perform semantic search using vector similarity.

        Args:
            index: The index to search ('leads', 'contacts', 'companies')
            query_text: Text query for hybrid search
            embedding: Vector embedding for semantic similarity (optional)
            size: Number of results to return
            filters: Optional filters (stage, source, tags, etc.)
        """
        if embedding:
            must_clauses = [
                {"vector": {"embedding": {"vector": embedding, "k": size, "num_candidates": 100}}}
            ]
            if query_text:
                must_clauses.append({"match": {"name": {"query": query_text, "fuzziness": "AUTO"}}})
            if filters:
                filter_clauses = [{"term": {k: v}} for k, v in filters.items()]
                query = {
                    "bool": {
                        "must": must_clauses,
                        "filter": filter_clauses,
                    }
                }
            else:
                query = {"bool": {"must": must_clauses}}
        else:
            match_query = {"match": {"name": {"query": query_text, "fuzziness": "AUTO"}}}
            if filters:
                filter_clauses = [{"term": {k: v}} for k, v in filters.items()]
                query = {"bool": {"must": [match_query], "filter": filter_clauses}}
            else:
                query = {"bool": {"must": [match_query]}}

        try:
            result = await self.es.search(index=index, query=query, size=size)
            hits = result.get("hits", {}).get("hits", [])
            return {
                "total": len(hits),
                "results": [
                    {
                        "id": hit["_id"],
                        "score": hit["_score"],
                        "data": hit["_source"],
                    }
                    for hit in hits
                ],
            }
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return {"total": 0, "results": [], "error": str(e)}

    async def search_leads(
        self,
        query: str,
        embedding: list[float] | None = None,
        stage: str | None = None,
        source: str | None = None,
        tags: list[str] | None = None,
        size: int = 10,
    ) -> dict[str, Any]:
        """Search leads semantically."""
        filters = {}
        if stage:
            filters["stage"] = stage
        if source:
            filters["source"] = source
        if tags:
            filters["tags"] = tags[0] if len(tags) == 1 else tags

        return await self.semantic_search(
            index=self.LEAD_INDEX,
            query_text=query,
            embedding=embedding,
            size=size,
            filters=filters if filters else None,
        )

    async def search_contacts(
        self,
        query: str,
        embedding: list[float] | None = None,
        company: str | None = None,
        title: str | None = None,
        size: int = 10,
    ) -> dict[str, Any]:
        """Search contacts semantically."""
        filters = {}
        if company:
            filters["company"] = company
        if title:
            filters["title"] = title

        return await self.semantic_search(
            index=self.CONTACT_INDEX,
            query_text=query,
            embedding=embedding,
            size=size,
            filters=filters if filters else None,
        )

    async def search_companies(
        self,
        query: str,
        embedding: list[float] | None = None,
        industry: str | None = None,
        size: str | None = None,
        size_limit: int = 10,
    ) -> dict[str, Any]:
        """Search companies semantically."""
        filters = {}
        if industry:
            filters["industry"] = industry
        if size:
            filters["size"] = size

        return await self.semantic_search(
            index=self.COMPANY_INDEX,
            query_text=query,
            embedding=embedding,
            size=size_limit,
            filters=filters if filters else None,
        )

    async def delete_document(self, index: str, doc_id: str) -> dict[str, Any]:
        """Delete a document from an index."""
        try:
            return await self.es.delete(index=index, id=doc_id)
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """Check search service health."""
        try:
            health = await self.es.health()
            return {"status": "healthy", "cluster": health.get("cluster_name")}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def get_query_embedding(self, query: str) -> list[float] | None:
        """Get embedding for a query using ML model service."""
        if not settings.ml_model_service_url:
            logger.warning("ML model service not configured")
            return None

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ml_model_service_url}/embed",
                    json={"text": query},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")
                else:
                    logger.warning(f"ML service returned {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get query embedding: {e}")
            return None

    async def rerank_results(self, results: dict[str, Any], query: str) -> dict[str, Any]:
        """Rerank search results using cross-encoder for better relevance."""
        if not results.get("results") or not settings.ml_model_service_url:
            return results

        try:
            import httpx
            documents = [
                {**r["data"], "text": f"{r['data'].get('name', '')} {r['data'].get('notes', '')}"}
                for r in results["results"]
            ]
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ml_model_service_url}/rerank",
                    json={"query": query, "documents": documents},
                )
                if response.status_code == 200:
                    data = response.json()
                    scores = data.get("scores", [])
                    for i, r in enumerate(results["results"]):
                        if i < len(scores):
                            r["rerank_score"] = scores[i]
                    results["results"].sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        except Exception as e:
            logger.warning(f"Reranking failed: {e}")

        return results


_search_service: SearchService | None = None


async def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
        await _search_service.ensure_indices()
    return _search_service
