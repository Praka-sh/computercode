from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "company_brain",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.ingestion.tasks",
        "app.extraction.tasks",
        "app.reconciliation.tasks",
        "app.skills.tasks",
        "app.agents.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    beat_schedule={},
)