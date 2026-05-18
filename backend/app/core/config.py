"""
Application Configuration
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "file:///app/data/agentic_crm.db"

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

    # HubSpot CRM
    hubspot_api_key: str = ""
    hubspot_portal_id: str = ""

    # Google Analytics 4
    ga4_measurement_id: str = ""
    ga4_api_secret: str = ""

    # Google Ads (conversion tracking)
    google_ads_conversion_id: str = ""
    google_ads_conversion_label_rfq: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ML Model Service
    ml_model_service_url: str = "http://localhost:8001"
    ml_inference_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_nested_delimiter = "__"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
