"""Core ingestion: normalise → dedupe → persist → enqueue classification.

Idempotency (TRD reliability): a provider message is processed at most once per
organisation. We rely on the unique index on emails(organization_id, message_id)
and an INSERT … ON CONFLICT DO NOTHING, so a retried webhook or an overlapping
poll never creates a duplicate or double-enqueues work.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..db import connection
from ..logging import get_logger
from .sanitize import sanitize_email_body
from .schemas import InboundEmail

log = get_logger(__name__)


@dataclass
class IngestResult:
    email_id: str | None
    created: bool          # False == duplicate, skipped
    injection_suspected: bool = False


def ingest_email(organization_id: str, account_id: str, inbound: InboundEmail) -> IngestResult:
    """Persist one inbound email idempotently and enqueue it for classification.

    Returns created=False (and no new work) if the message was already ingested.
    """
    clean = sanitize_email_body(inbound.body)

    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO emails (
                organization_id, account_id, message_id, thread_id,
                from_address, to_address, subject, body_clean, body_raw,
                received_at, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'new')
            ON CONFLICT (organization_id, message_id) DO NOTHING
            RETURNING id
            """,
            (
                organization_id,
                account_id,
                inbound.message_id,
                inbound.thread_id,
                inbound.from_address,
                inbound.to_address,
                inbound.subject,
                clean.text,
                inbound.body,
                inbound.received_at,
            ),
        ).fetchone()

    if row is None:
        log.info("ingest_duplicate_skipped", message_id=inbound.message_id, org=organization_id)
        return IngestResult(email_id=None, created=False)

    email_id = str(row["id"])

    # Audit + flag suspected prompt injection for human attention.
    _audit(organization_id, "ingested", {"type": "email", "id": email_id,
                                          "injection_suspected": clean.injection_suspected})
    if clean.injection_suspected:
        log.warning("ingest_injection_suspected", email_id=email_id, redactions=clean.redactions)

    _enqueue_classification(organization_id, email_id)
    log.info("ingest_created", email_id=email_id, message_id=inbound.message_id)
    return IngestResult(email_id=email_id, created=True, injection_suspected=clean.injection_suspected)


def _enqueue_classification(organization_id: str, email_id: str) -> None:
    """Create a job row and dispatch the classify task (Module 3 implements the
    actual classification; here we just wire the pipeline)."""
    from .. import jobs

    job_id = jobs.create_job("classify", organization_id=organization_id, payload={"email_id": email_id})
    try:
        from ..worker.tasks import classify_email

        classify_email.apply_async(kwargs={"job_id": job_id, "email_id": email_id,
                                            "organization_id": organization_id})
    except Exception as exc:  # broker momentarily unavailable — job stays queued
        log.warning("enqueue_classify_failed", email_id=email_id, error=str(exc))


def _audit(organization_id: str, action: str, entity: dict) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (organization_id, actor_id, action, entity) "
            "VALUES (%s, NULL, %s, %s)",
            (organization_id, action, json.dumps(entity)),
        )
