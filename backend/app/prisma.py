"""
Prisma Client singleton for Agentic CRM.
Use `from app.prisma import prisma, connect_prisma, disconnect_prisma` throughout the application.
"""
from app.generated import Prisma

# Module-level singleton — shared across the application lifecycle.
# Tests should call connect_prisma() once before running, or use the session_prisma fixture.
prisma = Prisma()

async def connect_prisma() -> None:
    """Connect to SQLite via Prisma on application startup."""
    if not prisma.is_connected():
        await prisma.connect()

async def disconnect_prisma() -> None:
    """Disconnect from Prisma on application shutdown."""
    if prisma.is_connected():
        await prisma.disconnect()