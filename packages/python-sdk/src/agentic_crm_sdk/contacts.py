"""
Contacts API client module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_crm_sdk.async_client import AsyncAgenticCRM

from agentic_crm_sdk.client import AgenticCRM


class ContactsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params: Any) -> Any:
        return self._client.get("/api/contacts", params=params)

    def get(self, contact_id: int) -> Any:
        return self._client.get(f"/api/contacts/{contact_id}")

    def create(self, data: dict) -> Any:
        return self._client.post("/api/contacts", json=data)

    def update(self, contact_id: int, data: dict) -> Any:
        return self._client.patch(f"/api/contacts/{contact_id}", json=data)

    def delete(self, contact_id: int) -> Any:
        return self._client.delete(f"/api/contacts/{contact_id}")


class AsyncContactsClient:
    def __init__(self, client: AsyncAgenticCRM):
        self._crm = client

    async def list(self, **params: Any) -> Any:
        return await self._crm.get("/api/contacts", params=params)

    async def get(self, contact_id: int) -> Any:
        return await self._crm.get(f"/api/contacts/{contact_id}")

    async def create(self, data: dict) -> Any:
        return await self._crm.post("/api/contacts", json=data)

    async def update(self, contact_id: int, data: dict) -> Any:
        return await self._crm.patch(f"/api/contacts/{contact_id}", json=data)

    async def delete(self, contact_id: int) -> Any:
        return await self._crm.delete(f"/api/contacts/{contact_id}")