"""The single entry point for all model calls.

Responsibilities (TRD §LLM correctness, Cost control, Observability):
  * Model routing: callers ask for a tier ("fast" / "smart"), not a model name.
  * Resilience: timeout + exponential-backoff retries on transient errors,
    with optional fallback to the fast model if the smart one fails.
  * Structured output: complete_json() forces JSON and validates it against a
    Pydantic model before returning — raw model text is never consumed.
  * Tracing: every call is logged (and sent to Langfuse if configured) with
    model, tokens, and latency.
"""
from __future__ import annotations

import contextlib
import contextvars
import json
from functools import lru_cache
from typing import Literal, Type, TypeVar

from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import get_settings
from ..logging import get_logger
from .base import ChatMessage, LLMError, LLMResponse, LLMTransientError
from .groq_provider import build_provider

log = get_logger(__name__)

ModelTier = Literal["fast", "smart"]
T = TypeVar("T", bound=BaseModel)

# Per-call usage attribution. Services bind (org, kind) so the wrapper can meter
# token usage to a tenant without threading it through every signature.
_usage_ctx: contextvars.ContextVar[dict | None] = contextvars.ContextVar("llm_usage_ctx", default=None)


@contextlib.contextmanager
def usage_context(organization_id: str | None, kind: str):
    token = _usage_ctx.set({"organization_id": organization_id, "kind": kind})
    try:
        yield
    finally:
        _usage_ctx.reset(token)


def _record_usage(model: str, resp: "LLMResponse") -> None:
    ctx = _usage_ctx.get()
    if not ctx or not ctx.get("organization_id"):
        return
    try:
        from ..db import connection

        with connection() as conn:
            conn.execute(
                "INSERT INTO llm_usage (organization_id, kind, model, prompt_tokens, completion_tokens) "
                "VALUES (%s, %s, %s, %s, %s)",
                (ctx["organization_id"], ctx.get("kind"), model, resp.prompt_tokens, resp.completion_tokens),
            )
    except Exception as exc:  # never let metering break a model call
        log.warning("llm_usage_record_failed", error=str(exc))


class LLM:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = build_provider(self.settings.llm_provider)
        self._langfuse = self._init_langfuse()

    def _init_langfuse(self):
        if not self.settings.langfuse_enabled:
            return None
        try:
            from langfuse import Langfuse

            return Langfuse(
                public_key=self.settings.langfuse_public_key,
                secret_key=self.settings.langfuse_secret_key,
                host=self.settings.langfuse_host,
            )
        except Exception as exc:  # pragma: no cover
            log.warning("langfuse_init_failed", error=str(exc))
            return None

    def resolve_model(self, tier: ModelTier) -> str:
        return self.settings.llm_model_smart if tier == "smart" else self.settings.llm_model_fast

    # -- core call with retries -------------------------------------------
    def complete(
        self,
        messages: list[ChatMessage],
        *,
        tier: ModelTier = "fast",
        temperature: float = 0.2,
        max_tokens: int | None = None,
        json_mode: bool = False,
        fallback_to_fast: bool = True,
        trace_name: str = "llm.complete",
    ) -> LLMResponse:
        model = self.resolve_model(tier)
        try:
            return self._complete_with_retry(
                messages, model=model, temperature=temperature,
                max_tokens=max_tokens, json_mode=json_mode, trace_name=trace_name,
            )
        except LLMError:
            if tier == "smart" and fallback_to_fast:
                log.warning("llm_fallback_to_fast", primary=model)
                return self._complete_with_retry(
                    messages, model=self.resolve_model("fast"), temperature=temperature,
                    max_tokens=max_tokens, json_mode=json_mode,
                    trace_name=f"{trace_name}.fallback",
                )
            raise

    def _complete_with_retry(self, messages, *, model, temperature, max_tokens, json_mode, trace_name) -> LLMResponse:
        attempt_call = retry(
            retry=retry_if_exception_type(LLMTransientError),
            stop=stop_after_attempt(self.settings.llm_max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            reraise=True,
        )(self.provider.complete)

        resp = attempt_call(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            timeout=self.settings.llm_timeout_seconds,
        )
        self._trace(trace_name, messages, resp, model)
        return resp

    # -- structured output -------------------------------------------------
    def complete_json(
        self,
        messages: list[ChatMessage],
        schema: Type[T],
        *,
        tier: ModelTier = "fast",
        temperature: float = 0.0,
        max_tokens: int | None = None,
        trace_name: str = "llm.complete_json",
    ) -> T:
        """Force JSON output and validate it against `schema`. Raises LLMError if
        the model returns something that doesn't conform."""
        resp = self.complete(
            messages, tier=tier, temperature=temperature, max_tokens=max_tokens,
            json_mode=True, trace_name=trace_name,
        )
        try:
            data = json.loads(resp.text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            log.warning("llm_json_validation_failed", error=str(exc), raw=resp.text[:500])
            raise LLMError(f"Model output failed schema validation: {exc}") from exc

    # -- streaming ---------------------------------------------------------
    def stream(self, messages: list[ChatMessage], *, tier: ModelTier = "smart", temperature: float = 0.3):
        model = self.resolve_model(tier)
        yield from self.provider.stream(
            messages, model=model, temperature=temperature,
            timeout=self.settings.llm_timeout_seconds,
        )

    # -- observability -----------------------------------------------------
    def _trace(self, name: str, messages: list[ChatMessage], resp: LLMResponse, model: str) -> None:
        log.info(
            "llm_call",
            name=name,
            model=model,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            latency_ms=resp.latency_ms,
        )
        _record_usage(model, resp)
        if self._langfuse is None:
            return
        try:
            gen = self._langfuse.generation(
                name=name,
                model=model,
                input=messages,
                output=resp.text,
                usage={
                    "input": resp.prompt_tokens,
                    "output": resp.completion_tokens,
                    "total": resp.total_tokens,
                },
            )
            gen.end()
        except Exception as exc:  # pragma: no cover
            log.warning("langfuse_trace_failed", error=str(exc))


@lru_cache
def get_llm() -> LLM:
    return LLM()
