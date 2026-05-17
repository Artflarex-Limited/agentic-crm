"""
Async Agentic CRM Python SDK Client.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import httpx

from agentic_crm_sdk.config import SDKConfig

if TYPE_CHECKING:
    from agentic_crm_sdk import leads, contacts, deals, activities, agents, sequences

logger = logging.getLogger(__name__)


class AsyncAgenticCRM:
    def __init__(self, config: SDKConfig | dict | None = None):
        if isinstance(config, dict):
            config = SDKConfig(**config)
        self.config = config or SDKConfig()

        self.base_url = self.config.base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.config.timeout,
            headers=self._build_headers(),
        )
        from agentic_crm_sdk import leads, contacts, deals, activities, agents, sequences
        self.leads = leads.AsyncLeadsClient(self)
        self.contacts = contacts.AsyncContactsClient(self)
        self.deals = deals.AsyncDealsClient(self)
        self.activities = activities.AsyncActivitiesClient(self)
        self.agents = agents.AsyncAgentsClient(self)
        self.sequences = sequences.AsyncSequencesClient(self)

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"agentic-crm-sdk/{__import__('agentic_crm_sdk').__version__}",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def request(
        self,
        method: str,
        path: str,
        retries: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        retries = retries if retries is not None else self.config.max_retries
        url = f"{self.base_url}{path}"

        for attempt in range(retries):
            try:
                response = await self._client.request(method, path, **kwargs)
                if response.status_code < 400:
                    return response
                if response.status_code >= 500:
                    if attempt < retries - 1:
                        await asyncio.sleep(self.config.retry_delay)
                        continue
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                elif response.status_code == 429:
                    if attempt < retries - 1:
                        await asyncio.sleep(self.config.retry_delay)
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
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise

        raise httpx.HTTPStatusError("Max retries exceeded", request=None, response=None)

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncAgenticCRM":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()