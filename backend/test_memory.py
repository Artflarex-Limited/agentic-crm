import asyncio
import os

os.environ["DATABASE_URL"] = "file::memory:?cache=shared"

from app.prisma import prisma


async def test():
    await prisma.connect()
    result = await prisma.query_raw("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables:", result)
asyncio.run(test())
