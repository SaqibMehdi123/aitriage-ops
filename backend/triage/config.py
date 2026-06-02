"""Centralised, validated settings loaded from the environment.

Every tunable lives here so the rest of the codebase never reads os.environ
directly. Loaded once and cached via get_settings().
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core ---
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql://triage:triage_dev_pw@localhost:5432/triage"

    # --- Redis / queue ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Auth (Supabase as identity provider) ---
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""

    # --- LLM ---
    llm_provider: Literal["groq", "openai", "anthropic"] = "groq"
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model_fast: str = "llama-3.1-8b-instant"
    llm_model_smart: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 3

    # --- Classification (Module 3) ---
    # Below this confidence the email is sent to the human-review lane
    # unclassified rather than guessed (TRD LLM-correctness).
    classification_confidence_threshold: float = 0.7

    # --- Embeddings / RAG (Module 4) ---
    # 'hash' is a free, offline, zero-dependency default so RAG works with no key
    # or model download. 'fastembed' is a free local semantic model; 'openai'
    # needs a key. Changing provider/dim requires re-embedding + a matching
    # vector(N) column (see db migrations).
    embedding_provider: Literal["hash", "fastembed", "openai"] = "hash"
    embedding_model: str = "BAAI/bge-small-en-v1.5"   # used by fastembed
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 384
    chunk_size: int = 800          # characters per chunk
    chunk_overlap: int = 150
    rag_top_k: int = 5

    # --- Observability ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    sentry_dsn: str = ""

    # --- Security ---
    token_encryption_key: str = ""

    # --- Mailbox OAuth (Module 2) ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/accounts/connect/google/callback"
    ms_graph_client_id: str = ""
    ms_graph_client_secret: str = ""
    ms_graph_tenant_id: str = "common"
    # Shared secret guarding the inbound mail webhook.
    mail_webhook_secret: str = ""

    # --- Routing (Module 6) ---
    # Optional Slack Incoming Webhook URL; routing notifications fire here when set.
    slack_webhook_url: str = ""

    # --- CRM logging ("Send & log to CRM") ---
    # webhook: POST the interaction to any URL (HubSpot/Zapier/Make/webhook.site).
    # hubspot: native — upsert the contact + attach a note (needs hubspot_token).
    crm_provider: Literal["none", "webhook", "hubspot"] = "none"
    crm_webhook_url: str = ""
    hubspot_token: str = ""

    # --- Analytics (Module 8) ---
    # Estimated minutes of manual triage+drafting saved per AI-handled email,
    # used for the "hours saved" headline metric.
    minutes_saved_per_email: int = 5

    # --- CORS (frontend origin) ---
    frontend_origin: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
