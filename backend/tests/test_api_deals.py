"""
API tests for deals endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_deals_empty(test_client: AsyncClient):
    response = await test_client.get("/api/deals/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_deal(test_client: AsyncClient, sample_contact, sample_company):
    response = await test_client.post(
        "/api/deals/",
        json={
            "contact_id": sample_contact.id,
            "company_id": sample_company.id,
            "name": "New Enterprise Deal",
            "value": 75000.0,
            "stage": "lead"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Enterprise Deal"
    assert data["value"] == 75000.0


@pytest.mark.asyncio
async def test_get_deal(test_client: AsyncClient, sample_deal):
    response = await test_client.get(f"/api/deals/{sample_deal.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Enterprise Deal"
    assert data["value"] == 50000.0


@pytest.mark.asyncio
async def test_get_deal_not_found(test_client: AsyncClient):
    response = await test_client.get("/api/deals/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_deal(test_client: AsyncClient, sample_deal):
    response = await test_client.put(
        f"/api/deals/{sample_deal.id}",
        json={"stage": "proposal", "value": 60000.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "proposal"
    assert data["value"] == 60000.0


@pytest.mark.asyncio
async def test_delete_deal(test_client: AsyncClient, sample_deal):
    response = await test_client.delete(f"/api/deals/{sample_deal.id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


@pytest.mark.asyncio
async def test_list_deals_with_data(test_client: AsyncClient, sample_deal):
    response = await test_client.get("/api/deals/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1