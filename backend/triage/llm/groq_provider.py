"""Groq provider (OpenAI-compatible chat completions, free tier).

Groq does not currently expose an embeddings endpoint — embeddings are handled
by a separate provider (see config.embedding_provider).
"""
from __future__ import annotations

import time
from typing import Iterator

from ..config import get_settings
from .base import ChatMessage, LLMResponse, LLMError, LLMTransientError, Provider


class GroqProvider:
    name = "groq"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY is not set.")
        # Imported lazily so the package imports even if the SDK isn't installed.
        from groq import Groq

        self._client = Groq(api_key=settings.groq_api_key)
        self._transient = self._transient_types()

    @staticmethod
    def _transient_types() -> tuple[type[Exception], ...]:
        try:
            from groq import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

            return (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)
        except Exception:  # pragma: no cover - SDK shape changes
            return ()

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        json_mode: bool = False,
        timeout: float = 30.0,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "timeout": timeout,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.perf_counter()
        try:
            resp = self._client.chat.completions.create(**kwargs)
        except self._transient as exc:  # type: ignore[misc]
            raise LLMTransientError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        latency_ms = int((time.perf_counter() - start) * 1000)

        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            latency_ms=latency_ms,
            raw=resp,
        )

    def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 30.0,
    ) -> Iterator[str]:
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "timeout": timeout,
            "stream": True,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        try:
            for chunk in self._client.chat.completions.create(**kwargs):
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except self._transient as exc:  # type: ignore[misc]
            raise LLMTransientError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc


def build_provider(provider_name: str) -> Provider:
    """Factory: return a provider instance for the configured name."""
    if provider_name == "groq":
        return GroqProvider()
    # OpenAI / Anthropic providers can be added here following the same shape.
    raise LLMError(
        f"Unsupported LLM_PROVIDER={provider_name!r}. "
        "Only 'groq' is wired up in the foundation; add a provider class to extend."
    )
