"""
Application Configuration
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - REQUIRED, no default
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security - REQUIRED, no default
    secret_key: str = ""

    # Webhook secret for inbound webhook authentication
    webhook_secret: str = ""

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_authenticated: str = "1000/minute"
    rate_limit_webhooks: str = "30/minute"

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

    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
