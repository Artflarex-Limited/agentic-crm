"""
Stub — SQLAlchemy database module was removed.
Application uses Prisma via app.prisma instead.
Only provides AsyncSessionLocal stub for legacy import compatibility.
"""
import os
from contextlib import asynccontextmanager


class AsyncSessionLocal:
    """Stub context manager — raises NotImplementedError.

    Use Prisma directly: from app.prisma import prisma
    """

    def __init__(self):
        raise NotImplementedError(
            "AsyncSessionLocal is a stub. "
            "Use Prisma via: from app.prisma import prisma"
        )

    async def __aenter__(self):
        raise NotImplementedError("Use Prisma instead")

    async def __aexit__(self, *args):
        raise NotImplementedError("Use Prisma instead")


@asynccontextmanager
async def get_db():
    """Stub — raises NotImplementedError."""
    raise NotImplementedError("Use app.prisma.prisma instead of SQLAlchemy get_db")


# Keep a minimal test engine for any code that needs it
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite+aiosqlite:///./agentic_crm.db"
)
