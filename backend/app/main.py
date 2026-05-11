"""
Agentic CRM - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Agentic CRM API",
    description="AI-First CRM — agents do the work, humans supervise",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
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


@app.get("/")
async def root():
    return {"message": "Agentic CRM API", "docs": "/docs"}
