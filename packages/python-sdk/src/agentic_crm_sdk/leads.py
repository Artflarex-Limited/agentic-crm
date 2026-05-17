"""
Leads API client module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_crm_sdk.async_client import AsyncAgenticCRM

from agentic_crm_sdk.client import AgenticCRM


class LeadsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params: Any) -> Any:
        return self._client.get("/api/leads", params=params)

    def get(self, lead_id: int) -> Any:
        return self._client.get(f"/api/leads/{lead_id}")

    def create(self, data: dict) -> Any:
        return self._client.post("/api/leads", json=data)

    def update(self, lead_id: int, data: dict) -> Any:
        return self._client.patch(f"/api/leads/{lead_id}", json=data)

    def delete(self, lead_id: int) -> Any:
        return self._client.delete(f"/api/leads/{lead_id}")

    def activities(self, lead_id: int) -> Any:
        return self._client.get(f"/api/leads/{lead_id}/activities")

    def add_note(self, lead_id: int, content: str) -> Any:
        return self._client.post(f"/api/leads/{lead_id}/notes", json={"content": content})


class AsyncLeadsClient:
    def __init__(self, client: AsyncAgenticCRM):
        self._crm = client

    async def list(self, **params: Any) -> Any:
        return await self._crm.get("/api/leads", params=params)

    async def get(self, lead_id: int) -> Any:
        return await self._crm.get(f"/api/leads/{lead_id}")

    async def create(self, data: dict) -> Any:
        return await self._crm.post("/api/leads", json=data)

    async def update(self, lead_id: int, data: dict) -> Any:
        return await self._crm.patch(f"/api/leads/{lead_id}", json=data)

    async def delete(self, lead_id: int) -> Any:
        return await self._crm.delete(f"/api/leads/{lead_id}")

    async def activities(self, lead_id: int) -> Any:
        return await self._crm.get(f"/api/leads/{lead_id}/activities")

    async def add_note(self, lead_id: int, content: str) -> Any:
        return await self._crm.post(f"/api/leads/{lead_id}/notes", json={"content": content})