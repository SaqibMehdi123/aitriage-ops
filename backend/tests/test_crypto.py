"""Token encryption roundtrip."""
from __future__ import annotations

from cryptography.fernet import Fernet

from triage.security.crypto import TokenCipher


def test_string_roundtrip():
    cipher = TokenCipher(Fernet.generate_key().decode())
    blob = cipher.encrypt("super-secret-access-token")
    assert blob != b"super-secret-access-token"          # actually encrypted
    assert cipher.decrypt(blob) == "super-secret-access-token"


def test_json_roundtrip():
    cipher = TokenCipher(Fernet.generate_key().decode())
    bundle = {"access_token": "a", "refresh_token": "r", "expires_at": 123.0}
    blob = cipher.encrypt_json(bundle)
    assert cipher.decrypt_json(blob) == bundle


def test_missing_key_raises():
    import pytest

    with pytest.raises(ValueError):
        TokenCipher("")
