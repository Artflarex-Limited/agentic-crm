"""
Deals API client module.
"""
from agentic_crm_sdk.client import AgenticCRM


class DealsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params):
        return self._client.get("/api/deals", params=params)

    def get(self, deal_id: int):
        return self._client.get(f"/api/deals/{deal_id}")

    def create(self, data: dict):
        return self._client.post("/api/deals", json=data)

    def update(self, deal_id: int, data: dict):
        return self._client.patch(f"/api/deals/{deal_id}", json=data)

    def delete(self, deal_id: int):
        return self._client.delete(f"/api/deals/{deal_id}")

    def activities(self, deal_id: int):
        return self._client.get(f"/api/deals/{deal_id}/activities")