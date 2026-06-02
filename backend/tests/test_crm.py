"""CRM logging dispatch tests (mocked HTTP, no network)."""
from __future__ import annotations

from triage.crm import service


class _FakeClient:
    last = {}

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, json=None):
        _FakeClient.last = {"url": url, "json": json}

        class R:
            status_code = 200

            def raise_for_status(self):
                pass

            @staticmethod
            def json():
                return {"id": "1"}

        return R()


def _settings(**kw):
    base = {"crm_provider": "none", "crm_webhook_url": "", "hubspot_token": ""}
    base.update(kw)
    return type("S", (), base)()


def test_none_is_noop(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: _settings(crm_provider="none"))
    assert service.log_interaction(contact_email="a@b.com", subject="x", category="Support", reply_body="hi") is False


def test_webhook_posts_normalised_payload(monkeypatch):
    monkeypatch.setattr(service.httpx, "Client", _FakeClient)
    monkeypatch.setattr(service, "get_settings", lambda: _settings(crm_provider="webhook", crm_webhook_url="http://crm.test/hook"))
    ok = service.log_interaction(contact_email="Jane <jane@acme.com>", subject="Refund", category="Billing", reply_body="done")
    assert ok is True
    assert _FakeClient.last["url"] == "http://crm.test/hook"
    assert _FakeClient.last["json"]["contact_email"] == "jane@acme.com"  # name stripped
    assert _FakeClient.last["json"]["category"] == "Billing"


def test_failure_is_swallowed(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("crm down")

    monkeypatch.setattr(service, "_webhook", boom)
    monkeypatch.setattr(service, "get_settings", lambda: _settings(crm_provider="webhook", crm_webhook_url="http://x"))
    # Must not raise — returns False so the send still succeeds.
    assert service.log_interaction(contact_email="a@b.com", subject="x", category=None, reply_body="hi") is False
