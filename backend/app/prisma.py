"""
Prisma Client singleton for Agentic CRM.
Use `from app.prisma import prisma` throughout the application.
"""
from app.generated import Prisma

# Singleton instance — import this wherever you need DB access
prisma = Prisma()

async def connect_prisma():
    """Connect to SQLite via Prisma on application startup."""
    if not prisma.is_connected:
        await prisma.connect()

async def disconnect_prisma():
    """Disconnect from Prisma on application shutdown."""
    if prisma.is_connected:
        await prisma.disconnect()