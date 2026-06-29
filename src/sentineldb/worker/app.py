"""
Celery app configuration.
"""
from __future__ import annotations

import logging

from celery import Celery

from sentineldb.core.config import settings

logger = logging.getLogger(__name__)

if settings.ENV != "development" and "@" not in settings.REDIS_URL:
    raise RuntimeError(
        "REDIS_URL lacks authentication (password). "
        "Redis authentication is required in non-development environments."
    )

celery_app = Celery(
    "sentineldb",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["sentineldb.worker.tasks"],
)

# R2: Celery task serialization uses JSON only. Pickle is prohibited.
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
