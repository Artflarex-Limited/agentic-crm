"""
Database connection and session management
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

_engine = None
_async_session_local = None


def get_engine():
    global _engine
    if _engine is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        _engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_async_session_local():
    global _async_session_local
    if _async_session_local is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            return None
        _async_session_local = async_sessionmaker(
            create_async_engine(
                database_url,
                echo=False,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
            ),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_local


def get_AsyncSessionLocal():
    return get_async_session_local()


AsyncSessionLocal = None


async def get_db():
    async_session = get_async_session_local()
    if async_session is None:
        raise ValueError("Database not configured. Set DATABASE_URL environment variable.")
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
