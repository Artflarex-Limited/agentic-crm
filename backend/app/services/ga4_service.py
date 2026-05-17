"""
Google Analytics 4 Service
Server-side event tracking via GA4 Measurement Protocol.
"""
import logging
import uuid

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class GA4Service:
    def __init__(self):
        self.measurement_id = settings.ga4_measurement_id
        self.api_secret = settings.ga4_api_secret
        self.base_url = "https://www.google-analytics.com/mp/collect"

    def _build_event_payload(
        self,
        event_name: str,
        client_id: str,
        user_id: str | None = None,
        params: dict | None = None,
    ) -> dict:
        """Build GA4 event payload."""
        _payload = {
            "client_id": client_id,
            "events": [{"name": event_name, "params": params or {}}],
        }

        if user_id:
            _payload["user_id"] = user_id

        return _payload

    async def track_event(
        self,
        event_name: str,
        client_id: str,
        user_id: str | None = None,
        params: dict | None = None,
    ) -> bool:
        """
        Send event to GA4 via Measurement Protocol.
        Returns True if successful.
        """
        if not self.measurement_id or not self.api_secret:
            logger.warning("GA4 not configured (measurement_id or api_secret missing)")
            return False

        try:
            payload = self._build_event_payload(event_name, client_id, user_id, params)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}?measurement_id={self.measurement_id}&api_secret={self.api_secret}",
                    json=payload,
                )

            if response.status_code == 204:
                logger.debug(f"GA4 event tracked: {event_name}")
                return True
            else:
                logger.warning(f"GA4 tracking failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"GA4 tracking error: {e}")
            return False

    async def track_lead_created(
        self,
        client_id: str,
        lead_id: int,
        source: str,
        utm_source: str | None = None,
        utm_campaign: str | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Track lead creation event."""
        params = {
            "lead_id": str(lead_id),
            "lead_source": source,
        }
        if utm_source:
            params["utm_source"] = utm_source
        if utm_campaign:
            params["utm_campaign"] = utm_campaign

        return await self.track_event(
            event_name="lead_created",
            client_id=client_id,
            user_id=user_email,
            params=params,
        )

    async def track_deal_stage_changed(
        self,
        client_id: str,
        deal_id: int,
        old_stage: str,
        new_stage: str,
        deal_value: float | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Track deal stage change event."""
        params = {
            "deal_id": str(deal_id),
            "old_stage": old_stage,
            "new_stage": new_stage,
        }
        if deal_value:
            params["deal_value"] = str(deal_value)

        return await self.track_event(
            event_name="deal_stage_changed",
            client_id=client_id,
            user_id=user_email,
            params=params,
        )

    async def track_email_sent(
        self,
        client_id: str,
        lead_id: int,
        subject: str,
        sequence_id: int | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Track email sent event."""
        params = {
            "lead_id": str(lead_id),
            "subject": subject,
        }
        if sequence_id:
            params["sequence_id"] = str(sequence_id)

        return await self.track_event(
            event_name="email_sent",
            client_id=client_id,
            user_id=user_email,
            params=params,
        )

    async def track_form_submission(
        self,
        client_id: str,
        form_name: str,
        lead_id: int | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Track web form submission event."""
        params = {"form_name": form_name}
        if lead_id:
            params["lead_id"] = str(lead_id)

        return await self.track_event(
            event_name="form_submission",
            client_id=client_id,
            user_id=user_email,
            params=params,
        )

    async def track_generate_rfq(
        self,
        client_id: str,
        deal_id: int,
        deal_value: float | None = None,
        lead_id: int | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Track RFQ (Request for Quote) generation event."""
        params: dict = {"deal_id": str(deal_id)}
        if deal_value:
            params["deal_value"] = str(deal_value)
        if lead_id:
            params["lead_id"] = str(lead_id)

        return await self.track_event(
            event_name="generate_rfq",
            client_id=client_id,
            user_id=user_email,
            params=params,
        )

    async def track_search_abandon(
        self,
        client_id: str,
        search_term: str | None = None,
        lead_id: int | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Track search abandonment event."""
        params: dict = {}
        if search_term:
            params["search_term"] = search_term
        if lead_id:
            params["lead_id"] = str(lead_id)

        return await self.track_event(
            event_name="search_abandon",
            client_id=client_id,
            user_id=user_email,
            params=params,
        )


def generate_ga_client_id() -> str:
    """Generate a unique GA client ID for anonymous users."""
    return str(uuid.uuid4())


async def get_ga4_service() -> GA4Service:
    return GA4Service()
