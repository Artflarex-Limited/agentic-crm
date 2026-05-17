"""
Activities API client module.
"""
from agentic_crm_sdk.client import AgenticCRM


class ActivitiesClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params):
        return self._client.get("/api/activities", params=params)

    def get(self, activity_id: int):
        return self._client.get(f"/api/activities/{activity_id}")

    def create(self, data: dict):
        return self._client.post("/api/activities", json=data)