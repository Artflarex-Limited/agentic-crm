"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://agentic_user:agentic_secret_pass@localhost:5432/agentic_crm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production-use-env-var"

    # SMTP / Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # LinkedIn
    linkedin_cookies: str = ""

    # Apollo.io (lead enrichment)
    apollo_api_key: str = ""

    # Twilio (phone)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    # Agent settings
    outreach_requires_approval: bool = True  # Human must approve before sending

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()