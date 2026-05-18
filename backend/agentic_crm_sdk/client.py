"""
Agentic CRM Python SDK Client.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from agentic_crm_sdk.config import SDKConfig

if TYPE_CHECKING:
    from agentic_crm_sdk import leads, contacts, deals, activities, agents, sequences

logger = logging.getLogger(__name__)


class AgenticCRM:
    def __init__(self, config: SDKConfig | dict | None = None):
        if isinstance(config, dict):
            config = SDKConfig(**config)
        self.config = config or SDKConfig()

        self.base_url = self.config.base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.config.timeout,
            headers=self._build_headers(),
        )
        from agentic_crm_sdk import leads, contacts, deals, activities, agents, sequences
        self.leads: leads.LeadsClient = leads.LeadsClient(self)
        self.contacts: contacts.ContactsClient = contacts.ContactsClient(self)
        self.deals: deals.DealsClient = deals.DealsClient(self)
        self.activities: activities.ActivitiesClient = activities.ActivitiesClient(self)
        self.agents: agents.AgentsClient = agents.AgentsClient(self)
        self.sequences: sequences.SequencesClient = sequences.SequencesClient(self)

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"agentic-crm-sdk/{__import__('agentic_crm_sdk').__version__}",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def request(
        self,
        method: str,
        path: str,
        retries: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        retries = retries if retries is not None else self.config.max_retries

        for attempt in range(retries):
            try:
                response = self._client.request(method, path, **kwargs)
                if response.status_code < 400:
                    return response
                if response.status_code >= 500:
                    if attempt < retries - 1:
                        continue
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                elif response.status_code == 429:
                    if attempt < retries - 1:
                        continue
                    raise httpx.HTTPStatusError(
                        f"Rate limited: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                else:
                    raise httpx.HTTPStatusError(
                        f"Client error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < retries - 1:
                    continue
                raise

        raise httpx.HTTPStatusError("Max retries exceeded", request=None, response=None)

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)