-- 0001 — Extensions, shared types, and convention helpers.
-- Conventions (from the Technical Foundation): every domain table has
-- id (UUID), organization_id, created_at, updated_at, deleted_at (soft delete).
-- Timestamps are timestamptz in UTC. We use a shared trigger to maintain updated_at.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for RAG embeddings

-- Maintain updated_at on every UPDATE.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── Shared enums ──────────────────────────────────────────────────────────
CREATE TYPE membership_role       AS ENUM ('owner', 'admin', 'agent');
CREATE TYPE email_account_provider AS ENUM ('gmail', 'outlook', 'imap');
CREATE TYPE email_account_status   AS ENUM ('connected', 'error', 'disconnected');
CREATE TYPE email_status           AS ENUM ('new', 'classified', 'drafted', 'sent', 'review');
CREATE TYPE urgency_level          AS ENUM ('low', 'normal', 'high');
CREATE TYPE draft_status           AS ENUM ('draft', 'edited', 'sent', 'discarded');
CREATE TYPE job_status             AS ENUM ('queued', 'running', 'succeeded', 'failed');
