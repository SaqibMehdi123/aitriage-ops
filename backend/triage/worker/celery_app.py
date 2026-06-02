"""Celery application — the queue that runs all long/bursty work off the
request cycle (ingestion, classification, drafting, embedding, routing).

Broker and result backend are both Redis. Acks-late + reject-on-worker-lost
give at-least-once delivery; tasks are written to be idempotent (keyed on
message-id etc.) so retries never double-act.
"""
from __future__ import annotations

from celery import Celery

from ..config import get_settings
from ..logging import configure_logging

settings = get_settings()
configure_logging()

celery = Celery(
    "triage",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["triage.worker.tasks"],
)

celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=300,          # hard kill at 5 min (latency budget per job)
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,  # fair dispatch for bursty, uneven jobs
    task_default_retry_delay=5,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Periodic mailbox polling (Module 2 continuous ingestion). Active when the
# worker is started with Beat enabled (`-B`). 60s is a conservative interval
# that respects provider + LLM rate limits; lower it for snappier ingestion.
celery.conf.beat_schedule = {
    "poll-mailboxes-every-60s": {
        "task": "triage.poll_mailboxes",
        "schedule": 60.0,
    },
    # Enforce per-org data retention once an hour.
    "purge-expired-hourly": {
        "task": "triage.purge_expired",
        "schedule": 3600.0,
    },
}
