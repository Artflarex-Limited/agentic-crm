"""
Sequences API client module.
"""
from agentic_crm_sdk.client import AgenticCRM


class SequencesClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params):
        return self._client.get("/api/sequences", params=params)

    def get(self, sequence_id: int):
        return self._client.get(f"/api/sequences/{sequence_id}")

    def create(self, data: dict):
        return self._client.post("/api/sequences", json=data)

    def update(self, sequence_id: int, data: dict):
        return self._client.patch(f"/api/sequences/{sequence_id}", json=data)

    def delete(self, sequence_id: int):
        return self._client.delete(f"/api/sequences/{sequence_id}")

    def enroll_lead(self, sequence_id: int, lead_id: int):
        return self._client.post(f"/api/sequences/{sequence_id}/enroll", json={"lead_id": lead_id})