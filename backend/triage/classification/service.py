"""Classification logic + persistence with confidence-threshold routing."""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..config import get_settings
from ..db import connection
from ..llm import LLMError, get_llm
from ..logging import get_logger
from .prompts import PROMPT_VERSION, build_messages
from .schemas import ClassificationResult

log = get_logger(__name__)


def model_version() -> str:
    s = get_settings()
    return f"{s.llm_provider}:{s.llm_model_fast}/{PROMPT_VERSION}"


def classify_text(subject: str | None, body: str | None, from_address: str | None) -> ClassificationResult:
    """Pure classification of email content. Used by both the pipeline and the
    eval runner. Raises LLMError if the model output can't be validated."""
    messages = build_messages(subject, body, from_address)
    return get_llm().complete_json(
        messages, ClassificationResult, tier="fast", trace_name="classify_email"
    )


@dataclass
class ClassifyOutcome:
    email_id: str
    category: str
    confidence: float
    urgency: str
    status: str          # resulting email status
    draftable: bool      # eligible to enqueue a draft


def classify_email(organization_id: str, email_id: str) -> ClassifyOutcome:
    """Classify a stored email, persist the result, and route by confidence.

    Routing (TRD): below threshold → 'review' (human lane, no draft); otherwise
    'classified'. Spam/Other never get an auto-draft.
    """
    with connection() as conn:
        email = conn.execute(
            "SELECT id, subject, body_clean, from_address FROM emails "
            "WHERE id = %s AND organization_id = %s AND deleted_at IS NULL",
            (email_id, organization_id),
        ).fetchone()
    if not email:
        raise ValueError(f"Email {email_id} not found for org {organization_id}")

    try:
        result = classify_text(email["subject"], email["body_clean"], email["from_address"])
    except LLMError as exc:
        # Never guess: record a zero-confidence Other and send to human review.
        log.warning("classification_failed_routing_to_review", email_id=email_id, error=str(exc))
        result = ClassificationResult(category="Other", confidence=0.0, urgency="normal",
                                      rationale="Automatic classification failed.")

    threshold = get_settings().classification_confidence_threshold
    below_threshold = result.confidence < threshold
    new_status = "review" if below_threshold else "classified"
    draftable = (not below_threshold) and result.category in ("Support", "Sales", "Billing")

    _persist(organization_id, email_id, result)
    _set_email_status(organization_id, email_id, new_status)
    _audit(organization_id, "classified", {
        "type": "email", "id": email_id, "category": result.category,
        "confidence": result.confidence, "urgency": result.urgency, "status": new_status,
    })
    log.info("email_classified", email_id=email_id, category=result.category,
             confidence=result.confidence, status=new_status)

    return ClassifyOutcome(
        email_id=email_id, category=result.category, confidence=result.confidence,
        urgency=result.urgency, status=new_status, draftable=draftable,
    )


def _persist(organization_id: str, email_id: str, result: ClassificationResult) -> None:
    """One active classification per email — update if present, else insert."""
    with connection() as conn, conn.transaction():
        existing = conn.execute(
            "SELECT id FROM classifications WHERE email_id = %s AND deleted_at IS NULL",
            (email_id,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE classifications SET category=%s, confidence=%s, urgency=%s, "
                "model=%s, rationale=%s WHERE id=%s",
                (result.category, result.confidence, result.urgency, model_version(),
                 result.rationale, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO classifications "
                "(organization_id, email_id, category, confidence, urgency, model, rationale) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (organization_id, email_id, result.category, result.confidence,
                 result.urgency, model_version(), result.rationale),
            )


def _set_email_status(organization_id: str, email_id: str, status: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE emails SET status = %s WHERE id = %s AND organization_id = %s",
            (status, email_id, organization_id),
        )


def _audit(organization_id: str, action: str, entity: dict) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (organization_id, actor_id, action, entity) "
            "VALUES (%s, NULL, %s, %s)",
            (organization_id, action, json.dumps(entity)),
        )
