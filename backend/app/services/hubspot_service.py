"""
HubSpot Service
Integration with HubSpot CRM for contact sync and tracking.
"""
import logging

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class HubSpotService:
    def __init__(self):
        self.api_key = settings.hubspot_api_key
        self.base_url = "https://api.hubapi.com"

    async def sync_contact(self, contact_id: int, email: str, properties: dict) -> dict | None:
        """
        Sync a contact to HubSpot.
        Creates or updates HubSpot contact and returns hubspot_contact_id.
        """
        if not self.api_key:
            logger.warning("HubSpot API key not configured")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            hubspot_properties = []
            for key, value in properties.items():
                if value is not None:
                    hubspot_properties.append({"property": key, "value": str(value)})

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    headers=headers,
                    json={
                        "properties": {
                            "email": email,
                            **{p["property"]: p["value"] for p in hubspot_properties},
                        }
                    },
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    hubspot_id = data.get("id")
                    logger.info(f"Contact synced to HubSpot: {hubspot_id}")
                    return {"hubspot_contact_id": hubspot_id}
                elif response.status_code == 409:
                    contact = await self.get_contact_by_email(email)
                    if contact:
                        return {"hubspot_contact_id": contact.get("id")}
                else:
                    logger.warning(f"HubSpot sync failed: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"HubSpot API error: {e}")
            return None

    async def get_contact_by_email(self, email: str) -> dict | None:
        """Get HubSpot contact by email."""
        if not self.api_key:
            return None

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts/search",
                    headers=headers,
                    json={
                        "filterGroups": [
                            {
                                "filters": [
                                    {"propertyName": "email", "operator": "EQ", "value": email}
                                ]
                            }
                        ]
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        return results[0]
                return None
        except Exception as e:
            logger.error(f"HubSpot search error: {e}")
            return None

    async def update_contact(self, hubspot_contact_id: str, properties: dict) -> bool:
        """Update a HubSpot contact."""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/crm/v3/objects/contacts/{hubspot_contact_id}",
                    headers=headers,
                    json={
                        "properties": {k: str(v) for k, v in properties.items() if v is not None}
                    },
                )

                if response.status_code == 200:
                    logger.info(f"HubSpot contact updated: {hubspot_contact_id}")
                    return True
                else:
                    logger.warning(f"HubSpot update failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"HubSpot update error: {e}")
            return False

    async def create_deal_association(self, hubspot_contact_id: str, deal_data: dict) -> str | None:
        """
        Create a deal in HubSpot and associate with contact.
        Returns hubspot deal id.
        """
        if not self.api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                deal_response = await client.post(
                    f"{self.base_url}/crm/v3/objects/deals",
                    headers=headers,
                    json={
                        "properties": {
                            "dealname": deal_data.get("name", "New Deal"),
                            "amount": str(deal_data.get("value", 0)),
                            "dealstage": deal_data.get("stage", "appointmentscheduled"),
                        }
                    },
                )

                if deal_response.status_code in (200, 201):
                    deal_id = deal_response.json().get("id")

                    assoc_response = await client.put(
                        f"{self.base_url}/crm/v4/objects/contacts/{hubspot_contact_id}/associations/deals/{deal_id}/deal_to_contact",
                        headers=headers,
                    )

                    if assoc_response.status_code in (200, 204):
                        logger.info(f"HubSpot deal created and associated: {deal_id}")
                        return deal_id

                return None
        except Exception as e:
            logger.error(f"HubSpot deal creation error: {e}")
            return None


async def get_hubspot_service() -> HubSpotService:
    return HubSpotService()