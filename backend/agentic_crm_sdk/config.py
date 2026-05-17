"""
SDK Configuration for Agentic CRM.
"""
from pydantic import BaseModel, Field


class SDKConfig(BaseModel):
    base_url: str = Field(default="http://localhost:8000", description="Base URL for the Agentic CRM API")
    api_key: str | None = Field(default=None, description="API key for authentication")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")