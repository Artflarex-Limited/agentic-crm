"""
API tests for leads endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_leads_empty(test_client: AsyncClient):
    response = await test_client.get("/api/leads/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_lead(test_client: AsyncClient, sample_contact):
    response = await test_client.post(
        "/api/leads/",
        json={
            "contact_id": sample_contact.id,
            "source": "email",
            "stage": "new",
            "score": 60,
            "tags": ["warm"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 60
    assert data["stage"] == "new"


@pytest.mark.asyncio
async def test_get_lead(test_client: AsyncClient, sample_lead):
    response = await test_client.get(f"/api/leads/{sample_lead.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 50
    assert data["contact"]["email"] == "john.doe@acme.com"


@pytest.mark.asyncio
async def test_get_lead_not_found(test_client: AsyncClient):
    response = await test_client.get("/api/leads/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_lead(test_client: AsyncClient, sample_lead):
    response = await test_client.put(
        f"/api/leads/{sample_lead.id}",
        json={"stage": "qualified", "score": 85}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "qualified"
    assert data["score"] == 85


@pytest.mark.asyncio
async def test_delete_lead(test_client: AsyncClient, sample_lead):
    response = await test_client.delete(f"/api/leads/{sample_lead.id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


@pytest.mark.asyncio
async def test_rescore_lead(test_client: AsyncClient, sample_lead):
    response = await test_client.post(f"/api/leads/{sample_lead.id}/score")
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == sample_lead.id
    assert "new_score" in data


@pytest.mark.asyncio
async def test_list_leads_with_data(test_client: AsyncClient, sample_lead):
    response = await test_client.get("/api/leads/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_lead_with_agent_assignment(test_client: AsyncClient, sample_contact, sample_agent):
    response = await test_client.post(
        "/api/leads/",
        json={
            "contact_id": sample_contact.id,
            "source": "linkedin",
            "stage": "new",
            "assigned_agent_id": sample_agent.id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["assigned_agent_id"] == sample_agent.id
