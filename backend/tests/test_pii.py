"""PII redaction unit tests (pure)."""
from __future__ import annotations

from triage.security.pii import redact_pii


def test_redacts_email():
    out = redact_pii("Contact me at jane.doe@example.com please")
    assert "jane.doe@example.com" not in out
    assert "[EMAIL]" in out


def test_redacts_phone():
    out = redact_pii("Call +1 (415) 555-2671 tomorrow")
    assert "555-2671" not in out
    assert "[PHONE]" in out


def test_redacts_card():
    out = redact_pii("card 4111 1111 1111 1111 on file")
    assert "4111" not in out
    assert "[CARD]" in out


def test_keeps_normal_text():
    out = redact_pii("I cannot log in to my account")
    assert out == "I cannot log in to my account"


def test_empty():
    assert redact_pii(None) == ""
    assert redact_pii("") == ""
