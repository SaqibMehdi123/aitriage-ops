-- 0006 — Audit log and background-jobs tracking.

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    actor_id        UUID REFERENCES users(id),    -- who (NULL = system)
    action          TEXT NOT NULL,                -- classified | drafted | sent | reassigned | ...
    entity          JSONB NOT NULL DEFAULT '{}',  -- affected record(s): {type, id, ...}
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX audit_logs_org_created_idx
    ON audit_logs (organization_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX audit_logs_action_idx ON audit_logs (organization_id, action);
CREATE TRIGGER trg_audit_logs_updated_at
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Background jobs: every long/bursty unit of work (ingest, classify, draft,
-- embed, route) is tracked here with status/progress/error for observability
-- and dead-letter handling.
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),   -- nullable for system jobs
    kind            TEXT NOT NULL,                -- ingest | classify | draft | embed | route
    status          job_status NOT NULL DEFAULT 'queued',
    progress        NUMERIC(4,3) NOT NULL DEFAULT 0,      -- 0.000–1.000
    payload         JSONB NOT NULL DEFAULT '{}',
    result          JSONB,
    error           TEXT,
    task_id         TEXT,                         -- Celery task id for correlation
    attempts        INT NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,
    CONSTRAINT progress_range CHECK (progress >= 0 AND progress <= 1)
);
CREATE INDEX jobs_org_status_idx ON jobs (organization_id, status) WHERE deleted_at IS NULL;
CREATE INDEX jobs_kind_status_idx ON jobs (kind, status);
CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
