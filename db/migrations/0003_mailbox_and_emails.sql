-- 0003 — Mailbox connections and ingested emails.

CREATE TABLE email_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    provider        email_account_provider NOT NULL,
    email_address   TEXT NOT NULL,
    -- OAuth access/refresh tokens, encrypted at rest (Fernet) before storage.
    oauth_tokens    BYTEA,
    status          email_account_status NOT NULL DEFAULT 'disconnected',
    last_synced_at  TIMESTAMPTZ,                  -- polling watermark
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX email_accounts_org_idx ON email_accounts (organization_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX email_accounts_org_address_unique
    ON email_accounts (organization_id, lower(email_address)) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_email_accounts_updated_at
    BEFORE UPDATE ON email_accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE emails (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    account_id      UUID NOT NULL REFERENCES email_accounts(id),
    message_id      TEXT NOT NULL,                -- provider id; idempotency key
    thread_id       TEXT,                         -- conversation grouping
    from_address    TEXT NOT NULL,
    to_address      TEXT,
    subject         TEXT,
    body_clean      TEXT,                         -- sanitised body (injection-stripped)
    body_raw        TEXT,                         -- original, for audit/debug
    received_at     TIMESTAMPTZ,                  -- provider timestamp
    status          email_status NOT NULL DEFAULT 'new',
    assignee_id     UUID REFERENCES users(id),    -- set by routing engine (Module 6)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
-- Idempotency: a provider message is processed at most once per org.
CREATE UNIQUE INDEX emails_org_message_unique ON emails (organization_id, message_id);
CREATE INDEX emails_org_status_idx   ON emails (organization_id, status) WHERE deleted_at IS NULL;
CREATE INDEX emails_org_received_idx  ON emails (organization_id, received_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX emails_assignee_idx     ON emails (assignee_id) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_emails_updated_at
    BEFORE UPDATE ON emails
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
