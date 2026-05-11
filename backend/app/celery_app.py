"""
Celery Application - Agent job queue
"""
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "agentic_crm",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.agents.lead_sourcing",
        "app.agents.email_outreach",
        "app.agents.research",
        "app.agents.follow_up",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)