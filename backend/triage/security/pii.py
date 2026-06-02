"""Best-effort PII redaction applied before sending content to an external LLM.

When an organisation enables PII redaction, emails/phones/cards/etc. are masked
so they never reach the model provider (TRD privacy). This is intentionally
conservative — it reduces exposure, it is not a guarantee of full anonymisation.
"""
from __future__ import annotations

import re

# Order matters: match the more specific/longer patterns (card, SSN) before the
# looser phone pattern, which would otherwise swallow a card-length digit run.
_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
    # Credit-card-like 13–16 digit runs (optionally grouped by spaces/dashes)
    (re.compile(r"(?<!\d)(?:\d[ -]?){13,16}(?<![ -])(?!\d)"), "[CARD]"),
    # US-SSN-like
    (re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"), "[ID]"),
    # Phone numbers (international-ish, 7+ digits with separators)
    (re.compile(r"(?<!\w)(\+?\d[\d\s().-]{5,}\d)(?!\w)"), "[PHONE]"),
]


def redact_pii(text: str | None) -> str:
    if not text:
        return ""
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out
