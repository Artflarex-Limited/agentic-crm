"""
API tests for contacts endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_contacts_empty(test_client: AsyncClient):
    response = await test_client.get("/api/contacts/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_contact(test_client: AsyncClient):
    response = await test_client.post(
        "/api/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Wilson",
            "email": "bob@example.com",
            "phone": "+1-555-9999",
            "title": "CTO"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Bob"
    assert data["email"] == "bob@example.com"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_contact(test_client: AsyncClient, sample_contact):
    response = await test_client.get(f"/api/contacts/{sample_contact.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "john.doe@acme.com"


@pytest.mark.asyncio
async def test_get_contact_not_found(test_client: AsyncClient):
    response = await test_client.get("/api/contacts/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_contact(test_client: AsyncClient, sample_contact):
    response = await test_client.put(
        f"/api/contacts/{sample_contact.id}",
        json={"first_name": "Johnny", "title": "Engineer"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Johnny"
    assert data["title"] == "Engineer"


@pytest.mark.asyncio
async def test_delete_contact(test_client: AsyncClient, sample_contact):
    response = await test_client.delete(f"/api/contacts/{sample_contact.id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    response = await test_client.get(f"/api/contacts/{sample_contact.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_contacts_with_data(test_client: AsyncClient, sample_contact):
    response = await test_client.get("/api/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "john.doe@acme.com"