"""
Activities API client module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_crm_sdk.async_client import AsyncAgenticCRM

from agentic_crm_sdk.client import AgenticCRM


class ActivitiesClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params: Any) -> Any:
        return self._client.get("/api/activities", params=params)

    def get(self, activity_id: int) -> Any:
        return self._client.get(f"/api/activities/{activity_id}")

    def create(self, data: dict) -> Any:
        return self._client.post("/api/activities", json=data)


class AsyncActivitiesClient:
    def __init__(self, client: AsyncAgenticCRM):
        self._crm = client

    async def list(self, **params: Any) -> Any:
        return await self._crm.get("/api/activities", params=params)

    async def get(self, activity_id: int) -> Any:
        return await self._crm.get(f"/api/activities/{activity_id}")

    async def create(self, data: dict) -> Any:
        return await self._crm.post("/api/activities", json=data)