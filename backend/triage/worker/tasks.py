"""Task definitions + a job-lifecycle base task.

`TrackedTask` wires Celery's execution into the `jobs` table: when a task that
was enqueued with a job_id runs, the job is moved running → succeeded/failed
automatically, and uncaught exceptions are recorded for dead-letter handling.

Feature modules (classification, drafting, routing, ingestion) will add their
own @celery.task functions here in later modules. For the foundation we ship a
`ping` task to prove the API → Redis → worker → Postgres path end to end.
"""
from __future__ import annotations

from celery import Task

from .. import jobs
from ..logging import get_logger
from .celery_app import celery

log = get_logger(__name__)


class TrackedTask(Task):
    """Base task that syncs lifecycle to the jobs table when a `job_id` kwarg
    is supplied."""

    def before_start(self, task_id, args, kwargs):  # noqa: D401
        job_id = kwargs.get("job_id")
        if job_id:
            jobs.mark_running(job_id, task_id=task_id)

    def on_success(self, retval, task_id, args, kwargs):
        job_id = kwargs.get("job_id")
        if job_id:
            result = retval if isinstance(retval, dict) else {"result": retval}
            jobs.mark_succeeded(job_id, result)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get("job_id")
        if job_id:
            jobs.mark_failed(job_id, str(exc))


@celery.task(base=TrackedTask, bind=True, name="triage.ping")
def ping(self, *, job_id: str | None = None, message: str = "pong") -> dict:
    """Foundation smoke-test task. Returns the message and the worker hostname."""
    log.info("ping_task", message=message, job_id=job_id)
    return {"message": message, "worker": self.request.hostname}


@celery.task(name="triage.poll_mailboxes")
def poll_mailboxes() -> dict:
    """Periodic poller (Celery Beat): enqueue a sync for every connected mailbox.

    This is what makes real-email ingestion automatic — it runs on a schedule and
    fans out one sync_account task per connected, non-IMAP-manual account."""
    from ..db import connection

    enqueued = 0
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, organization_id FROM email_accounts "
            "WHERE status = 'connected' AND deleted_at IS NULL AND email_address <> 'manual@inbox.local'"
        ).fetchall()
    for r in rows:
        sync_account.apply_async(kwargs={"organization_id": str(r["organization_id"]),
                                         "account_id": str(r["id"])})
        enqueued += 1
    if enqueued:
        log.info("poll_mailboxes_enqueued", count=enqueued)
    return {"enqueued": enqueued}


@celery.task(name="triage.poll_mailboxes")
def poll_mailboxes() -> dict:
    """Periodic poller (Celery Beat): enqueue a sync for every connected mailbox.

    Runs across all organisations; each mailbox is synced idempotently so new
    messages are ingested without duplicates."""
    from ..db import connection

    with connection() as conn:
        accounts = conn.execute(
            "SELECT id, organization_id FROM email_accounts "
            "WHERE status = 'connected' AND deleted_at IS NULL"
        ).fetchall()

    enqueued = 0
    for a in accounts:
        org = str(a["organization_id"])
        aid = str(a["id"])
        job_id = jobs.create_job("ingest", organization_id=org, payload={"account_id": aid, "poll": True})
        sync_account.apply_async(kwargs={"organization_id": org, "account_id": aid, "job_id": job_id})
        enqueued += 1
    log.info("poll_mailboxes", accounts=enqueued)
    return {"enqueued": enqueued}


@celery.task(base=TrackedTask, bind=True, name="triage.sync_account", max_retries=3)
def sync_account(self, *, organization_id: str, account_id: str, job_id: str | None = None) -> dict:
    """Poll a connected mailbox and ingest new messages (Module 2)."""
    from ..ingestion.sync import sync_account as run_sync

    try:
        return run_sync(organization_id, account_id)
    except Exception as exc:
        # Retry transient provider/network failures with backoff; the job row
        # records the failure if retries are exhausted.
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))


@celery.task(base=TrackedTask, bind=True, name="triage.classify_email", max_retries=2)
def classify_email(self, *, email_id: str, organization_id: str, job_id: str | None = None) -> dict:
    """Classify an ingested email and route by confidence (Module 3).

    On success, eligible emails (high-confidence Support/Sales/Billing) are
    enqueued for reply drafting (Module 5 implements the drafting itself)."""
    from ..classification.service import classify_email as run_classify

    outcome = run_classify(organization_id, email_id)

    # Every classified email is routed (so it is owned), then drafted if eligible.
    job_route = jobs.create_job("route", organization_id=organization_id, payload={"email_id": email_id})
    route_email.apply_async(kwargs={"job_id": job_route, "email_id": email_id,
                                    "organization_id": organization_id})

    if outcome.draftable:
        job_id2 = jobs.create_job("draft", organization_id=organization_id, payload={"email_id": email_id})
        draft_email.apply_async(kwargs={"job_id": job_id2, "email_id": email_id,
                                        "organization_id": organization_id})

    return {
        "email_id": email_id, "category": outcome.category,
        "confidence": outcome.confidence, "status": outcome.status,
    }


@celery.task(base=TrackedTask, bind=True, name="triage.route_email", max_retries=2)
def route_email(self, *, email_id: str, organization_id: str, job_id: str | None = None) -> dict:
    """Apply routing rules → assignee + CRM action + Slack notify (Module 6)."""
    from ..routing.service import route_email as run_route

    try:
        outcome = run_route(organization_id, email_id)
        return {"email_id": email_id, "rule_id": outcome.rule_id,
                "assignee_id": outcome.assignee_id, "slack": outcome.slack_notified}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))


@celery.task(base=TrackedTask, bind=True, name="triage.embed_document", max_retries=2)
def embed_document(self, *, organization_id: str, doc_id: str, job_id: str | None = None) -> dict:
    """Chunk + embed an uploaded knowledge document into pgvector (Module 4)."""
    from ..knowledge.service import embed_document as run_embed

    try:
        result = run_embed(organization_id, doc_id)
        return {"doc_id": result.doc_id, "chunks": result.chunks}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))


@celery.task(base=TrackedTask, bind=True, name="triage.draft_email", max_retries=2)
def draft_email(self, *, email_id: str, organization_id: str, job_id: str | None = None) -> dict:
    """Generate a RAG-grounded reply draft for a classified email (Module 5)."""
    from ..drafting.service import draft_for_email

    try:
        result = draft_for_email(organization_id, email_id)
        return {"email_id": email_id, "draft_id": result.draft_id, "sources": len(result.sources)}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))
