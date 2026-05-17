"""
Agents API client module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_crm_sdk.async_client import AsyncAgenticCRM

from agentic_crm_sdk.client import AgenticCRM


class AgentsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params: Any) -> Any:
        return self._client.get("/api/agents", params=params)

    def get(self, agent_id: int) -> Any:
        return self._client.get(f"/api/agents/{agent_id}")

    def update_status(self, agent_id: int, status: str) -> Any:
        return self._client.patch(f"/api/agents/{agent_id}", json={"status": status})

    def pause(self, agent_id: int) -> Any:
        return self.update_status(agent_id, "paused")

    def resume(self, agent_id: int) -> Any:
        return self.update_status(agent_id, "active")


class AsyncAgentsClient:
    def __init__(self, client: AsyncAgenticCRM):
        self._crm = client

    async def list(self, **params: Any) -> Any:
        return await self._crm.get("/api/agents", params=params)

    async def get(self, agent_id: int) -> Any:
        return await self._crm.get(f"/api/agents/{agent_id}")

    async def update_status(self, agent_id: int, status: str) -> Any:
        return await self._crm.patch(f"/api/agents/{agent_id}", json={"status": status})

    async def pause(self, agent_id: int) -> Any:
        return await self.update_status(agent_id, "paused")

    async def resume(self, agent_id: int) -> Any:
        return await self.update_status(agent_id, "active")