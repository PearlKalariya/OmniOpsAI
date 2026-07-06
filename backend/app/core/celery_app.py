"""Celery application (Redis broker).

Run a worker from backend/:

    celery -A app.core.celery_app worker --loglevel=info --pool=solo

--pool=solo keeps one process so the embedding/OCR models load once
(prefork would load a copy per child — several GB each).
Results live in Postgres (document.status), so no result backend.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "omniops",
    broker=settings.redis_url,
    include=["app.tasks.ingestion"],
)

celery_app.conf.update(
    task_acks_late=True,  # re-deliver if the worker dies mid-task
    worker_prefetch_multiplier=1,  # don't hoard tasks while one is running
    broker_connection_retry_on_startup=True,
    task_ignore_result=True,
)
