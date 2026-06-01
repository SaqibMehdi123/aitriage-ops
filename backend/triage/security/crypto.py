"""Symmetric encryption for secrets at rest — OAuth tokens in email_accounts.

Uses Fernet (AES-128-CBC + HMAC). The key comes from TOKEN_ENCRYPTION_KEY; in a
real deployment that key lives in a secrets manager, never in code (TRD security
conventions). Generate one with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from __future__ import annotations

import json
from functools import lru_cache

from cryptography.fernet import Fernet

from ..config import get_settings


class TokenCipher:
    def __init__(self, key: str):
        if not key:
            raise ValueError(
                "TOKEN_ENCRYPTION_KEY is not set — cannot encrypt OAuth tokens at rest."
            )
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, token: bytes) -> str:
        return self._fernet.decrypt(bytes(token)).decode("utf-8")

    def encrypt_json(self, data: dict) -> bytes:
        """Encrypt a token bundle (access/refresh/expiry) for the bytea column."""
        return self.encrypt(json.dumps(data, separators=(",", ":")))

    def decrypt_json(self, token: bytes) -> dict:
        return json.loads(self.decrypt(token))


@lru_cache
def get_cipher() -> TokenCipher:
    return TokenCipher(get_settings().token_encryption_key)
