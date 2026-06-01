"""Knowledge-document lifecycle: create → chunk → embed → store."""
from __future__ import annotations

from dataclasses import dataclass

from ..config import get_settings
from ..db import connection
from ..logging import get_logger
from .chunking import chunk_text
from .embeddings import get_embedder, to_pgvector

log = get_logger(__name__)


@dataclass
class EmbedResult:
    doc_id: str
    chunks: int


def create_document(organization_id: str, title: str, content: str, *, source: str | None = None) -> str:
    """Insert a knowledge_docs row (status 'pending') with its raw text so the
    async embed step can read it cross-process. Returns the doc id."""
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO knowledge_docs (organization_id, title, source, status, raw_content) "
            "VALUES (%s, %s, %s, 'pending', %s) RETURNING id",
            (organization_id, title, source or title, content),
        ).fetchone()
    return str(row["id"])


def embed_document(organization_id: str, doc_id: str, content: str | None = None) -> EmbedResult:
    """Chunk + embed + persist the document's chunks; mark the doc 'synced'."""
    settings = get_settings()
    if content is None:
        with connection() as conn:
            row = conn.execute(
                "SELECT raw_content FROM knowledge_docs WHERE id = %s AND organization_id = %s",
                (doc_id, organization_id),
            ).fetchone()
        content = row["raw_content"] if row else None
    if content is None:
        raise ValueError("No content available to embed for this document.")

    _set_status(organization_id, doc_id, "embedding")
    try:
        chunks = chunk_text(content, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
        if chunks:
            vectors = get_embedder().embed(chunks)
            _store_chunks(organization_id, doc_id, chunks, vectors)
        _set_status(organization_id, doc_id, "synced")
    except Exception as exc:
        _set_status(organization_id, doc_id, "error")
        log.error("embed_document_failed", doc_id=doc_id, error=str(exc))
        raise

    log.info("document_embedded", doc_id=doc_id, chunks=len(chunks))
    return EmbedResult(doc_id=doc_id, chunks=len(chunks))


def _store_chunks(organization_id: str, doc_id: str, chunks: list[str], vectors: list[list[float]]) -> None:
    with connection() as conn, conn.transaction():
        # Replace any prior chunks for idempotent re-embedding.
        conn.execute("DELETE FROM knowledge_chunks WHERE doc_id = %s AND organization_id = %s",
                     (doc_id, organization_id))
        for i, (text, vec) in enumerate(zip(chunks, vectors)):
            conn.execute(
                "INSERT INTO knowledge_chunks (organization_id, doc_id, chunk_index, content, embedding) "
                "VALUES (%s, %s, %s, %s, %s::vector)",
                (organization_id, doc_id, i, text, to_pgvector(vec)),
            )


def _set_status(organization_id: str, doc_id: str, status: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE knowledge_docs SET status = %s WHERE id = %s AND organization_id = %s",
            (status, doc_id, organization_id),
        )
