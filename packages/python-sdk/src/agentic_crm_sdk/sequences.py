"""
Sequences API client module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_crm_sdk.async_client import AsyncAgenticCRM

from agentic_crm_sdk.client import AgenticCRM


class SequencesClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params: Any) -> Any:
        return self._client.get("/api/sequences", params=params)

    def get(self, sequence_id: int) -> Any:
        return self._client.get(f"/api/sequences/{sequence_id}")

    def create(self, data: dict) -> Any:
        return self._client.post("/api/sequences", json=data)

    def update(self, sequence_id: int, data: dict) -> Any:
        return self._client.patch(f"/api/sequences/{sequence_id}", json=data)

    def delete(self, sequence_id: int) -> Any:
        return self._client.delete(f"/api/sequences/{sequence_id}")

    def enroll_lead(self, sequence_id: int, lead_id: int) -> Any:
        return self._client.post(f"/api/sequences/{sequence_id}/enroll", json={"lead_id": lead_id})


class AsyncSequencesClient:
    def __init__(self, client: AsyncAgenticCRM):
        self._crm = client

    async def list(self, **params: Any) -> Any:
        return await self._crm.get("/api/sequences", params=params)

    async def get(self, sequence_id: int) -> Any:
        return await self._crm.get(f"/api/sequences/{sequence_id}")

    async def create(self, data: dict) -> Any:
        return await self._crm.post("/api/sequences", json=data)

    async def update(self, sequence_id: int, data: dict) -> Any:
        return await self._crm.patch(f"/api/sequences/{sequence_id}", json=data)

    async def delete(self, sequence_id: int) -> Any:
        return await self._crm.delete(f"/api/sequences/{sequence_id}")

    async def enroll_lead(self, sequence_id: int, lead_id: int) -> Any:
        return await self._crm.post(f"/api/sequences/{sequence_id}/enroll", json={"lead_id": lead_id})