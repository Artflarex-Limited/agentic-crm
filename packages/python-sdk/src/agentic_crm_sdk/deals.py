"""
Deals API client module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_crm_sdk.async_client import AsyncAgenticCRM

from agentic_crm_sdk.client import AgenticCRM


class DealsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params: Any) -> Any:
        return self._client.get("/api/deals", params=params)

    def get(self, deal_id: int) -> Any:
        return self._client.get(f"/api/deals/{deal_id}")

    def create(self, data: dict) -> Any:
        return self._client.post("/api/deals", json=data)

    def update(self, deal_id: int, data: dict) -> Any:
        return self._client.patch(f"/api/deals/{deal_id}", json=data)

    def delete(self, deal_id: int) -> Any:
        return self._client.delete(f"/api/deals/{deal_id}")

    def activities(self, deal_id: int) -> Any:
        return self._client.get(f"/api/deals/{deal_id}/activities")


class AsyncDealsClient:
    def __init__(self, client: AsyncAgenticCRM):
        self._crm = client

    async def list(self, **params: Any) -> Any:
        return await self._crm.get("/api/deals", params=params)

    async def get(self, deal_id: int) -> Any:
        return await self._crm.get(f"/api/deals/{deal_id}")

    async def create(self, data: dict) -> Any:
        return await self._crm.post("/api/deals", json=data)

    async def update(self, deal_id: int, data: dict) -> Any:
        return await self._crm.patch(f"/api/deals/{deal_id}", json=data)

    async def delete(self, deal_id: int) -> Any:
        return await self._crm.delete(f"/api/deals/{deal_id}")

    async def activities(self, deal_id: int) -> Any:
        return await self._crm.get(f"/api/deals/{deal_id}/activities")