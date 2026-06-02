"""Knowledge base endpoints — upload (file or JSON), list, delete, search.

Uploads create a doc then enqueue embedding off the request cycle. Search is a
debug/inspection endpoint over the same retrieval used to ground drafts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context, require_admin
from ...db import OrgScopedDb
from ..ratelimit import rate_limit
from ...knowledge.extract import UnsupportedDocument, extract_text
from ...knowledge.retrieval import retrieve
from ...knowledge.service import create_document
from ... import jobs

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _enqueue_embed(organization_id: str, doc_id: str) -> str:
    from ...worker.tasks import embed_document

    job_id = jobs.create_job("embed", organization_id=organization_id, payload={"doc_id": doc_id})
    embed_document.apply_async(kwargs={"job_id": job_id, "organization_id": organization_id, "doc_id": doc_id})
    return job_id


class DocOut(BaseModel):
    id: str
    title: str
    source: str | None
    status: str
    created_at: str | None = None


class UploadResponse(BaseModel):
    doc_id: str
    job_id: str
    status: str


@router.get("", response_model=list[DocOut])
def list_docs(ctx: AuthContext = Depends(get_auth_context)) -> list[DocOut]:
    rows = OrgScopedDb(ctx.organization_id).fetch_all(
        "knowledge_docs", order_by="created_at DESC"
    )
    return [
        DocOut(id=str(r["id"]), title=r["title"], source=r.get("source"), status=r["status"],
               created_at=r["created_at"].isoformat() if r.get("created_at") else None)
        for r in rows
    ]


class TextUploadIn(BaseModel):
    title: str
    content: str
    source: str | None = None


@router.post("/text", response_model=UploadResponse)
def upload_text(body: TextUploadIn, ctx: AuthContext = Depends(require_admin),
                _rl: AuthContext = Depends(rate_limit("kb_upload", 30))) -> UploadResponse:
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content is empty.")
    doc_id = create_document(ctx.organization_id, body.title, body.content, source=body.source)
    job_id = _enqueue_embed(ctx.organization_id, doc_id)
    return UploadResponse(doc_id=doc_id, job_id=job_id, status="embedding")


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    ctx: AuthContext = Depends(require_admin),
    _rl: AuthContext = Depends(rate_limit("kb_upload", 30)),
) -> UploadResponse:
    data = await file.read()
    try:
        text = extract_text(file.filename or "upload.txt", data)
    except UnsupportedDocument as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text in the document.")
    doc_id = create_document(ctx.organization_id, title or file.filename or "Untitled",
                             text, source=file.filename)
    job_id = _enqueue_embed(ctx.organization_id, doc_id)
    return UploadResponse(doc_id=doc_id, job_id=job_id, status="embedding")


@router.delete("/{doc_id}")
def delete_doc(doc_id: str, ctx: AuthContext = Depends(require_admin)) -> dict:
    db = OrgScopedDb(ctx.organization_id)
    if not db.fetch_one("knowledge_docs", {"id": doc_id}):
        raise HTTPException(status_code=404, detail="Document not found")
    # Soft-delete the doc and its chunks (chunks excluded from retrieval).
    from ...db import connection

    with connection() as conn:
        conn.execute("UPDATE knowledge_chunks SET deleted_at = now() WHERE doc_id = %s AND organization_id = %s",
                     (doc_id, ctx.organization_id))
    db.soft_delete("knowledge_docs", doc_id)
    return {"status": "deleted", "doc_id": doc_id}


class SearchIn(BaseModel):
    query: str
    k: int | None = None


class SearchHit(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    score: float
    title: str | None = None
    source: str | None = None


@router.post("/search", response_model=list[SearchHit])
def search(body: SearchIn, ctx: AuthContext = Depends(get_auth_context)) -> list[SearchHit]:
    hits = retrieve(ctx.organization_id, body.query, k=body.k)
    return [
        SearchHit(chunk_id=h.chunk_id, doc_id=h.doc_id, content=h.content,
                  score=round(h.score, 4), title=h.title, source=h.source)
        for h in hits
    ]
