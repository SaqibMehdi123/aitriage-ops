"""Authenticated context + a foundation smoke-test for the job pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...auth import AuthContext, get_auth_context
from ...db import OrgScopedDb
from ... import jobs

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    user_id: str
    email: str
    organization_id: str
    organization_name: str | None
    role: str


@router.get("/me", response_model=MeResponse)
def me(ctx: AuthContext = Depends(get_auth_context)) -> MeResponse:
    """Return the caller's identity and active organization. Also confirms the
    full auth → JIT-provisioning → org-scoped data path works."""
    db = OrgScopedDb(ctx.organization_id)
    org = db.fetch_one("organizations", {"id": ctx.organization_id})
    return MeResponse(
        user_id=ctx.user_id,
        email=ctx.email,
        organization_id=ctx.organization_id,
        organization_name=org["name"] if org else None,
        role=ctx.role,
    )


class Member(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    role: str


@router.get("/members", response_model=list[Member])
def list_members(ctx: AuthContext = Depends(get_auth_context)) -> list[Member]:
    """Org teammates — used for assignee dropdowns in the queue and rules editor."""
    from ...db import connection

    with connection() as conn:
        rows = conn.execute(
            "SELECT u.id, u.email, u.full_name, m.role FROM memberships m "
            "JOIN users u ON u.id = m.user_id "
            "WHERE m.organization_id = %s AND m.deleted_at IS NULL ORDER BY u.email",
            (ctx.organization_id,),
        ).fetchall()
    return [Member(user_id=str(r["id"]), email=r["email"], full_name=r["full_name"], role=r["role"]) for r in rows]


class PingResponse(BaseModel):
    job_id: str
    task_id: str


@router.post("/jobs/ping", response_model=PingResponse)
def enqueue_ping(ctx: AuthContext = Depends(get_auth_context)) -> PingResponse:
    """Enqueue the foundation `ping` task and track it as a job. Lets you verify
    the API → Redis → worker → Postgres(jobs) loop without any feature code."""
    # Imported here so the API can boot even if Celery/Redis is momentarily down.
    from ...worker.tasks import ping

    job_id = jobs.create_job("ping", organization_id=ctx.organization_id, payload={"by": ctx.user_id})
    async_result = ping.apply_async(kwargs={"job_id": job_id, "message": "pong"})
    return PingResponse(job_id=job_id, task_id=async_result.id)


class JobStatusResponse(BaseModel):
    id: str
    kind: str
    status: str
    progress: float
    result: dict | None = None
    error: str | None = None


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, ctx: AuthContext = Depends(get_auth_context)) -> JobStatusResponse:
    db = OrgScopedDb(ctx.organization_id)
    row = db.fetch_one("jobs", {"id": job_id})
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        id=str(row["id"]),
        kind=row["kind"],
        status=row["status"],
        progress=float(row["progress"]),
        result=row.get("result"),
        error=row.get("error"),
    )
