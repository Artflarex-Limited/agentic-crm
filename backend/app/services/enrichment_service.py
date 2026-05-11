"""
Enrichment Service
Apollo.io integration, data enrichment.
"""
from app.core.config import get_settings
import httpx
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class EnrichmentService:
    def __init__(self):
        self.apollo_api_key = settings.apollo_api_key
        self.base_url = "https://api.apollo.io/v1"

    async def enrich_contact(self, email: str) -> dict:
        """
        Enrich a contact by email using Apollo.io API.
        Returns dict of enriched data or empty dict.
        """
        if not self.apollo_api_key:
            logger.warning("Apollo.io API key not configured")
            return {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/contacts/find",
                    params={"email": email},
                    headers={"api_key": self.apollo_api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    contact_data = data.get("contact", {})
                    return {
                        "first_name": contact_data.get("first_name"),
                        "last_name": contact_data.get("last_name"),
                        "title": contact_data.get("title"),
                        "company_name": contact_data.get("organization", {}).get("name"),
                        "company_domain": contact_data.get("organization", {}).get("domain"),
                        "linkedin_url": contact_data.get("linkedin_url"),
                        "phone": contact_data.get("phone_number"),
                    }
                else:
                    logger.warning(f"Apollo.io enrichment failed: {response.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"Apollo.io API error: {e}")
            return {}

    async def enrich_company(self, company_name: str) -> dict:
        """
        Enrich a company by name using Apollo.io API.
        """
        if not self.apollo_api_key:
            logger.warning("Apollo.io API key not configured")
            return {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/organizations/find",
                    params={"name": company_name},
                    headers={"api_key": self.apollo_api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    org_data = data.get("organization", {})
                    return {
                        "domain": org_data.get("domain"),
                        "industry": org_data.get("industry"),
                        "size": org_data.get("employee_count"),
                        "linkedin_url": org_data.get("linkedin_url"),
                    }
                else:
                    logger.warning(f"Apollo.io company enrichment failed: {response.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"Apollo.io company API error: {e}")
            return {}

    async def search_contacts(self, query: str, limit: int = 10) -> list:
        """
        Search for contacts matching a query.
        """
        if not self.apollo_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/contacts/search",
                    json={"query": query, "per_page": limit},
                    headers={"api_key": self.apollo_api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("contacts", [])
                else:
                    return []
        except Exception as e:
            logger.error(f"Apollo.io search error: {e}")
            return []


async def get_enrichment_service() -> EnrichmentService:
    return EnrichmentService()