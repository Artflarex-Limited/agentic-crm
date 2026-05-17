"""
Agentic CRM MCP Server

Model Context Protocol server that exposes Agentic CRM tools to AI agents.
Uses the Agentic CRM REST API to perform operations.
"""
import os
from typing import Any

import httpx
from pydantic import BaseModel
from pydantic_settings import BaseSettings

__version__ = "0.1.0"


class Settings(BaseSettings):
    agentic_crm_api_url: str = "http://localhost:8000"
    agentic_crm_api_key: str = ""
    timeout: float = 30.0

    class Config:
        env_prefix = "AGENTIC_CRM_"


settings = Settings()


class MCPToolInput(BaseModel):
    tool: str
    parameters: dict[str, Any] = {}


def get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.agentic_crm_api_url,
        headers={"Authorization": f"Bearer {settings.agentic_crm_api_key}"} if settings.agentic_crm_api_key else {},
        timeout=settings.timeout,
    )


async def call_api(method: str, path: str, **kwargs) -> dict[str, Any]:
    async with get_http_client() as client:
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()