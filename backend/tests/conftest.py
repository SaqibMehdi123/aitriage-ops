"""Test setup: ensure a token-encryption key exists before settings are read.

The container exports an empty TOKEN_ENCRYPTION_KEY via env_file, so we must
overwrite (not setdefault) when it is missing or blank — before any triage
module instantiates and caches settings.
"""
from __future__ import annotations

import os

from cryptography.fernet import Fernet

if not os.environ.get("TOKEN_ENCRYPTION_KEY"):
    os.environ["TOKEN_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ.setdefault("APP_ENV", "development")
