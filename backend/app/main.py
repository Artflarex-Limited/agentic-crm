"""
Agentic CRM - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.clients import (
    check_all_health,
    check_database_health,
    check_redis_health,
    check_elasticsearch_health,
)
from app.api import (
    activities,
    agents,
    companies,
    contacts,
    dashboard,
    deals,
    leads,
    sequences,
    webhooks,
)
from app.db.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Agentic CRM API",
    description="AI-First CRM — agents do the work, humans supervise",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(deals.router, prefix="/api/deals", tags=["deals"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(sequences.router, prefix="/api/sequences", tags=["sequences"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/health/detailed")
async def health_detailed():
    health_status = await check_all_health()
    return {
        "status": "healthy" if all(s.get("status") == "healthy" for s in health_status.values()) else "degraded",
        "services": health_status,
    }


@app.get("/health/db")
async def health_db():
    status = await check_database_health()
    return status


@app.get("/health/redis")
async def health_redis():
    status = await check_redis_health()
    return status


@app.get("/health/elasticsearch")
async def health_elasticsearch():
    status = await check_elasticsearch_health()
    return status


@app.get("/")
async def root():
    return {"message": "Agentic CRM API", "docs": "/docs"}
