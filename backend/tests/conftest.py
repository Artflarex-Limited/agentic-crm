"""
Pytest fixtures for Agentic CRM backend tests
Prisma-based: uses app.prisma directly (no SQLAlchemy).
"""
import asyncio
import os
import subprocess
import tempfile
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.prisma import prisma

# Use a temporary FILE-based SQLite DB per session
_test_db_file = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"file:{_test_db_file}"


# ─── Session-scoped Prisma lifecycle (once per pytest session) ───────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def session_prisma():
    """Run prisma db push once, then connect once for all tests in this session."""
    # Push schema to the temp DB (idempotent — only creates tables once)
    subprocess.run(
        ["python", "-m", "prisma", "db", "push", "--skip-generate",
         "--schema", "prisma/schema.prisma"],
        env={**os.environ},
        check=True,
    )
    await prisma.connect()
    yield
    await prisma.disconnect()
    # Cleanup temp DB file
    try:
        os.unlink(_test_db_file)
    except OSError:
        pass


# ─── Function-scoped test client ────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def test_client(session_prisma) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for FastAPI routes that use app.prisma directly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ─── Sample data helpers (Prisma-based) ──────────────────────────────────────

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
            "company_id": sample_company.id,
            "first_name": "John",
            "last_name": "Doe",
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
            "contact_id": sample_contact.id,
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
            "contact_id": sample_contact.id,
            "company_id": sample_company.id,
            "name": "Acme Enterprise Deal",
            "value": 50000.0,
            "stage": DealStage.QUALIFIED.value,
            "expected_close_date": datetime.utcnow() + timedelta(days=30),
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
            "lead_id": sample_lead.id,
            "agent_id": sample_agent.id,
            "type": ActivityType.EMAIL_SENT.value,
            "content": "Sent welcome email",
        }
    )
    return activity


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}


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