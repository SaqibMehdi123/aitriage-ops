"""Chunking + hash-embedder unit tests (pure, no DB or network)."""
from __future__ import annotations

from triage.knowledge.chunking import chunk_text
from triage.knowledge.embeddings import HashEmbedder


def test_short_text_is_single_chunk():
    assert chunk_text("just a short note") == ["just a short note"]


def test_empty_text_yields_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_long_text_splits_with_overlap():
    para = ("Alpha beta gamma delta. " * 60).strip()   # > chunk_size
    chunks = chunk_text(para, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


def test_paragraph_boundaries_preferred():
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
    chunks = chunk_text(text, chunk_size=30, overlap=5)
    assert len(chunks) >= 2


def test_hash_embedder_is_deterministic_and_unit_length():
    emb = HashEmbedder(dim=384)
    a1 = emb.embed(["password reset help"])[0]
    a2 = emb.embed(["password reset help"])[0]
    assert a1 == a2
    norm = sum(v * v for v in a1) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_hash_embedder_similar_text_scores_higher():
    emb = HashEmbedder(dim=384)

    def cos(a, b):
        return sum(x * y for x, y in zip(a, b))

    query = emb.embed(["how do I reset my password"])[0]
    close = emb.embed(["resetting your password steps"])[0]
    far = emb.embed(["enterprise pricing and volume discounts"])[0]
    assert cos(query, close) > cos(query, far)
