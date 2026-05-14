"""
Database client utilities for PostgreSQL, Redis, and Elasticsearch.
Shared across all FastAPI microservices.
"""
import logging
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


_engine = None
_async_session_local = None


def get_engine():
    global _engine
    if _engine is None:
        database_url = settings.database_url
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
        database_url = settings.database_url
        if not database_url:
            return None
        _async_session_local = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_local


@asynccontextmanager
async def get_db_session():
    """Context manager for database sessions."""
    session_local = get_async_session_local()
    if session_local is None:
        raise ValueError("Database not configured")
    async with session_local() as session:
        try:
            yield session
        finally:
            await session.close()


class RedisClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> redis.Redis:
        """Connect to Redis."""
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> str | None:
        """Get value from Redis."""
        client = await self.connect()
        return await client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire: int | None = None,
    ) -> bool:
        """Set value in Redis with optional expiration."""
        client = await self.connect()
        return await client.set(key, value, ex=expire)

    async def delete(self, key: str) -> int:
        """Delete key from Redis."""
        client = await self.connect()
        return await client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        client = await self.connect()
        return await client.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment counter in Redis."""
        client = await self.connect()
        return await client.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        client = await self.connect()
        return await client.expire(key, seconds)

    async def lpush(self, key: str, *values: str) -> int:
        """Push to list."""
        client = await self.connect()
        return await client.lpush(key, *values)

    async def rpop(self, key: str) -> str | None:
        """Pop from list."""
        client = await self.connect()
        return await client.rpop(key)


class ElasticsearchClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, hosts: list[str] | None = None) -> AsyncElasticsearch:
        """Connect to Elasticsearch."""
        if self._client is None:
            from app.core.config import get_settings
            settings = get_settings()
            es_hosts = hosts or settings.elasticsearch_hosts or ["http://localhost:9200"]
            self._client = AsyncElasticsearch(hosts=es_hosts)
        return self._client

    async def close(self):
        """Close Elasticsearch connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def search(
        self,
        index: str,
        query: dict[str, Any],
        size: int = 10,
    ) -> dict[str, Any]:
        """Search Elasticsearch index."""
        client = await self.connect()
        return await client.search(index=index, body=query, size=size)

    async def index(
        self,
        index: str,
        document: dict[str, Any],
        id: str | None = None,
    ) -> dict[str, Any]:
        """Index document in Elasticsearch."""
        client = await self.connect()
        return await client.index(index=index, body=document, id=id)

    async def delete(self, index: str, id: str) -> dict[str, Any]:
        """Delete document from Elasticsearch."""
        client = await self.connect()
        return await client.delete(index=index, id=id)

    async def health(self) -> dict[str, Any]:
        """Check Elasticsearch cluster health."""
        client = await self.connect()
        return await client.cluster.health()


redis_client = RedisClient()
es_client = ElasticsearchClient()


async def check_database_health() -> dict[str, Any]:
    """Check PostgreSQL connection health."""
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        return {"status": "healthy", "service": "postgresql"}
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {"status": "unhealthy", "service": "postgresql", "error": str(e)}


async def check_redis_health() -> dict[str, Any]:
    """Check Redis connection health."""
    try:
        client = await redis_client.connect()
        await client.ping()
        return {"status": "healthy", "service": "redis"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "service": "redis", "error": str(e)}


async def check_elasticsearch_health() -> dict[str, Any]:
    """Check Elasticsearch connection health."""
    try:
        health = await es_client.health()
        return {"status": "healthy", "service": "elasticsearch", "cluster": health.get("cluster_name")}
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return {"status": "unhealthy", "service": "elasticsearch", "error": str(e)}


async def check_all_health() -> dict[str, Any]:
    """Check health of all external services."""
    import asyncio
    results = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_elasticsearch_health(),
        return_exceptions=True,
    )
    services = ["postgresql", "redis", "elasticsearch"]
    health_status = {}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            health_status[services[i]] = {"status": "unhealthy", "error": str(result)}
        else:
            health_status[services[i]] = result
    return health_status