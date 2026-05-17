"""
Contacts API client module.
"""
from agentic_crm_sdk.client import AgenticCRM


class ContactsClient:
    def __init__(self, client: AgenticCRM):
        self._client = client

    def list(self, **params):
        return self._client.get("/api/contacts", params=params)

    def get(self, contact_id: int):
        return self._client.get(f"/api/contacts/{contact_id}")

    def create(self, data: dict):
        return self._client.post("/api/contacts", json=data)

    def update(self, contact_id: int, data: dict):
        return self._client.patch(f"/api/contacts/{contact_id}", json=data)

    def delete(self, contact_id: int):
        return self._client.delete(f"/api/contacts/{contact_id}")