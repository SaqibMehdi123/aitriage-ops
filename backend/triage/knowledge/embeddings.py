"""Pluggable text embeddings.

Providers:
  * hash      — feature-hashing bag-of-words, L2-normalised. Free, offline, no
                deps. Captures lexical overlap so retrieval is meaningful and
                fully testable without a key or model download. Default.
  * fastembed — free local semantic model (ONNX, no torch). Lazy-imported.
  * openai    — hosted embeddings; needs OPENAI_API_KEY.

All return unit-length vectors of length settings.embedding_dim so cosine
similarity (pgvector <=>) is well-behaved.
"""
from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache
from typing import Protocol

from ..config import get_settings
from ..logging import get_logger

log = get_logger(__name__)
_TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _l2(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class HashEmbedder:
    """Deterministic feature-hashing embedder (the hashing trick)."""

    def __init__(self, dim: int):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _TOKEN.findall((text or "").lower()):
            h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:8], "big")
            idx = h % self.dim
            sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
            vec[idx] += sign
        return _l2(vec)


class FastEmbedEmbedder:
    def __init__(self, model: str, dim: int):
        from fastembed import TextEmbedding  # lazy: optional dependency

        self._model = TextEmbedding(model_name=model)
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._model.embed(texts)]


class OpenAIEmbedder:
    def __init__(self, model: str, dim: int):
        self.model = model
        self.dim = dim
        self._key = get_settings().openai_api_key
        if not self._key:
            raise RuntimeError("OPENAI_API_KEY required for the openai embedding provider.")

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._key}"},
                json={"model": self.model, "input": texts},
            )
            resp.raise_for_status()
            return [d["embedding"] for d in resp.json()["data"]]


@lru_cache
def get_embedder() -> Embedder:
    s = get_settings()
    if s.embedding_provider == "openai":
        return OpenAIEmbedder(s.openai_embedding_model, s.embedding_dim)
    if s.embedding_provider == "fastembed":
        return FastEmbedEmbedder(s.embedding_model, s.embedding_dim)
    return HashEmbedder(s.embedding_dim)


def to_pgvector(vec: list[float]) -> str:
    """Format a vector as a pgvector literal: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
