"""Knowledge base + RAG (Module 4).

Documents are chunked, embedded into pgvector, and retrieved top-k (org-scoped,
metadata-filterable) to ground reply drafts. Embeddings are pluggable; the
default is a free, offline hash embedder so retrieval works with no API key.
"""
from .embeddings import get_embedder
from .retrieval import retrieve
from .service import create_document, embed_document

__all__ = ["get_embedder", "retrieve", "create_document", "embed_document"]
