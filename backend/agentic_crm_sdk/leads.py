"""
Leads API client module.
"""
from agentic_crm_sdk.client import AgenticCRM


class LeadsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params):
        return self._client.get("/api/leads", params=params)

    def get(self, lead_id: int):
        return self._client.get(f"/api/leads/{lead_id}")

    def create(self, data: dict):
        return self._client.post("/api/leads", json=data)

    def update(self, lead_id: int, data: dict):
        return self._client.patch(f"/api/leads/{lead_id}", json=data)

    def delete(self, lead_id: int):
        return self._client.delete(f"/api/leads/{lead_id}")

    def activities(self, lead_id: int):
        return self._client.get(f"/api/leads/{lead_id}/activities")

    def add_note(self, lead_id: int, content: str):
        return self._client.post(f"/api/leads/{lead_id}/notes", json={"content": content})