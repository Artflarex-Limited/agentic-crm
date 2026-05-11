"""
Pytest fixtures for Agentic CRM backend tests
"""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.models.models import (
    Company, Contact, Lead, Deal, Agent, Sequence, Activity, AuditLog,
    LeadSource, LeadStage, DealStage, AgentRole, AgentStatus, ActivityType
)


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_company(db_session: AsyncSession) -> Company:
    company = Company(
        name="Acme Corp",
        domain="acme.com",
        industry="Technology",
        size="100-500",
        linkedin_url="https://linkedin.com/company/acme",
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def sample_contact(db_session: AsyncSession, sample_company: Company) -> Contact:
    contact = Contact(
        company_id=sample_company.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@acme.com",
        phone="+1-555-0100",
        title="VP Engineering",
        linkedin_url="https://linkedin.com/in/johndoe",
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def sample_lead(db_session: AsyncSession, sample_contact: Contact) -> Lead:
    lead = Lead(
        contact_id=sample_contact.id,
        source=LeadSource.EMAIL,
        stage=LeadStage.NEW,
        score=50,
        tags=["warm", "enterprise"],
        notes="Interested in enterprise plan",
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead


@pytest_asyncio.fixture
async def sample_deal(db_session: AsyncSession, sample_contact: Contact, sample_company: Company) -> Deal:
    deal = Deal(
        contact_id=sample_contact.id,
        company_id=sample_company.id,
        name="Acme Enterprise Deal",
        value=50000.0,
        stage=DealStage.QUALIFIED,
        expected_close_date=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    return deal


@pytest_asyncio.fixture
async def sample_agent(db_session: AsyncSession) -> Agent:
    agent = Agent(
        name="Outreach Agent",
        role=AgentRole.OUTREACH,
        status=AgentStatus.ACTIVE,
        config={"max_emails_per_day": 50, "approval_required": True},
        description="Handles outbound email campaigns",
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def sample_sequence(db_session: AsyncSession) -> Sequence:
    sequence = Sequence(
        name="Welcome Sequence",
        description="Onboarding email sequence",
        steps=[
            {"type": "email", "subject": "Welcome to Agentic CRM", "content": "Hello!", "delay_days": 0},
            {"type": "email", "subject": "Quick follow-up", "content": "Checking in", "delay_days": 2},
        ],
        is_active=True,
    )
    db_session.add(sequence)
    await db_session.commit()
    await db_session.refresh(sequence)
    return sequence


@pytest_asyncio.fixture
async def sample_activity(db_session: AsyncSession, sample_lead: Lead, sample_agent: Agent) -> Activity:
    activity = Activity(
        lead_id=sample_lead.id,
        agent_id=sample_agent.id,
        type=ActivityType.EMAIL_SENT,
        content="Sent welcome email to lead",
        metadata={"email_id": "msg-123"},
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)
    return activity


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}