"""
Pytest fixtures for Agentic CRM backend tests
Prisma-based: uses app.prisma directly (no SQLAlchemy).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.prisma import connect_prisma, disconnect_prisma, prisma


# Dynamically find the backend directory (works locally and in CI)
def get_backend_dir():
    """Return path to the backend directory."""
    return str(Path(__file__).parent.parent.absolute())


def get_new_db_file():
    return tempfile.mktemp(suffix=".db")


@pytest_asyncio.fixture
async def session_prisma():
    """Push schema and connect Prisma per test function."""
    _test_db_file = get_new_db_file()
    os.environ["DATABASE_URL"] = f"file:{_test_db_file}"

    backend_dir = get_backend_dir()
    subprocess.run(
        [sys.executable, "-m", "prisma", "db", "push", "--skip-generate",
         "--schema", "prisma/schema.prisma"],
        env={**os.environ},
        check=True,
        cwd=backend_dir,
        capture_output=True,
    )
    await connect_prisma()
    yield
    await disconnect_prisma()
    try:
        os.unlink(_test_db_file)
    except OSError:
        pass


@pytest_asyncio.fixture
async def test_client(session_prisma) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def sample_company(session_prisma):
    company = await prisma.company.create(
        data={
            "name": "Acme Corp",
            "domain": "acme.com",
            "industry": "Technology",
            "size": "100-500",
        }
    )
    return company


@pytest_asyncio.fixture
async def sample_contact(sample_company):
    contact = await prisma.contact.create(
        data={
            "companyId": sample_company.id,
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@acme.com",
            "phone": "+1-555-0100",
            "title": "VP Engineering",
        }
    )
    return contact


@pytest_asyncio.fixture
async def sample_lead(sample_contact):
    from app.enums import LeadSource, LeadStage
    lead = await prisma.lead.create(
        data={
            "contactId": sample_contact.id,
            "source": LeadSource.EMAIL.value,
            "stage": LeadStage.NEW.value,
            "score": 50,
            "tags": "warm,enterprise",
            "notes": "Interested in enterprise plan",
        }
    )
    return lead


@pytest_asyncio.fixture
async def sample_deal(sample_contact, sample_company):
    from app.enums import DealStage
    deal = await prisma.deal.create(
        data={
            "contactId": sample_contact.id,
            "companyId": sample_company.id,
            "name": "Acme Enterprise Deal",
            "value": 50000.0,
            "stage": DealStage.QUALIFIED.value,
            "expectedCloseDate": datetime.now(UTC) + timedelta(days=30),
        }
    )
    return deal


@pytest_asyncio.fixture
async def sample_agent(session_prisma):
    from app.enums import AgentRole, AgentStatus
    agent = await prisma.agent.create(
        data={
            "name": "Outreach Agent",
            "role": AgentRole.OUTREACH.value,
            "status": AgentStatus.ACTIVE.value,
            "config": '{"max_emails_per_day": 50}',
        }
    )
    return agent


@pytest_asyncio.fixture
async def sample_activity(sample_lead, sample_agent):
    from app.enums import ActivityType
    activity = await prisma.activity.create(
        data={
            "leadId": sample_lead.id,
            "agentId": sample_agent.id,
            "type": ActivityType.EMAIL_SENT.value,
            "content": "Sent welcome email",
        }
    )
    return activity


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}


@pytest_asyncio.fixture
async def sample_sequence(session_prisma):
    import json
    sequence = await prisma.sequence.create(
        data={
            "name": "Test Sequence",
            "description": "Test sequence",
            "steps": json.dumps([
                {"type": "email", "subject": "Hello", "content": "Hi!", "delay_days": 1},
                {"type": "email", "subject": "Follow up", "content": "Bump", "delay_days": 3},
            ]),
            "isActive": True
        }
    )
    return sequence


@pytest_asyncio.fixture
async def sample_product_category(session_prisma):
    category = await prisma.productcategory.create(
        data={
            "family": "Machinery",
            "cls": "cnc",
            "commodity": "CNC Milling Machine",
            "description": "CNC milling machine",
            "keywords": "cnc,milling,machine",
        }
    )
    return category
