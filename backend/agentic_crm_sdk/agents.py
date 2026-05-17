"""
Agents API client module.
"""
from agentic_crm_sdk.client import AgenticCRM


class AgentsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params):
        return self._client.get("/api/agents", params=params)

    def get(self, agent_id: int):
        return self._client.get(f"/api/agents/{agent_id}")

    def update_status(self, agent_id: int, status: str):
        return self._client.patch(f"/api/agents/{agent_id}", json={"status": status})

    def pause(self, agent_id: int):
        return self.update_status(agent_id, "paused")

    def resume(self, agent_id: int):
        return self.update_status(agent_id, "active")