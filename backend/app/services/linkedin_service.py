"""
LinkedIn Service
Connection requests, messaging via Apollo.io LinkedIn integration.
"""
from app.core.config import get_settings
import httpx
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class LinkedInService:
    def __init__(self):
        self.apollo_api_key = settings.apollo_api_key
        self.linkedin_cookies = settings.linkedin_cookies

    async def send_connection_request(
        self, profile_url: str, message: str = ""
    ) -> dict:
        """
        Send a LinkedIn connection request.
        Uses Apollo.io or direct LinkedIn API.
        """
        if not self.apollo_api_key:
            logger.warning("Apollo.io API key not configured")
            return {"status": "error", "message": "API key not configured"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.apollo.io/v1/social_actions/linkedin_connect",
                    json={
                        "profile_url": profile_url,
                        "message": message,
                    },
                    headers={"api_key": self.apollo_api_key},
                )

                if response.status_code == 200:
                    return {"status": "sent", "data": response.json()}
                else:
                    return {"status": "error", "message": f"API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"LinkedIn connection request failed: {e}")
            return {"status": "error", "message": str(e)}

    async def send_message(
        self, profile_url: str, message: str
    ) -> dict:
        """
        Send a LinkedIn message to a connection.
        """
        if not self.apollo_api_key:
            return {"status": "error", "message": "API key not configured"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.apollo.io/v1/social_actions/linkedin_message",
                    json={
                        "profile_url": profile_url,
                        "message": message,
                    },
                    headers={"api_key": self.apollo_api_key},
                )

                if response.status_code == 200:
                    return {"status": "sent", "data": response.json()}
                else:
                    return {"status": "error", "message": f"API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"LinkedIn message failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_profile_info(self, profile_url: str) -> dict:
        """
        Get LinkedIn profile information.
        """
        if not self.apollo_api_key:
            return {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.apollo.io/v1/social_actions/linkedin_profile",
                    params={"profile_url": profile_url},
                    headers={"api_key": self.apollo_api_key},
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
        except Exception as e:
            logger.error(f"LinkedIn profile lookup failed: {e}")
            return {}


async def get_linkedin_service() -> LinkedInService:
    return LinkedInService()