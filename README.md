# AI Inbox Triage + Reply Router

An event-driven pipeline with human-in-the-loop review. It connects to a shared
support/sales inbox, classifies every email by intent, drafts a context-aware
reply grounded in the company's knowledge base (RAG), and routes it to the right
person or CRM. A human reviews and sends with one click.

This repository currently implements **Module 0 (Foundation)** and
**Module 1 (Auth & multi-tenancy)** from the modular plan in the project brief.

---

## Architecture

```
Next.js (App Router, TS, Tailwind)        ← review UI + thin reads
        │  Authorization: Bearer <Supabase JWT>
        ▼
FastAPI (Python)  ──enqueue──▶  Redis  ──▶  Celery workers
        │                                        │
        └──────────────┬─────────────────────────┘
                       ▼
        PostgreSQL + pgvector  (emails, drafts, classifications,
                                routing rules, knowledge, jobs, audit log)
```

- **Auth/identity:** Supabase (issues JWTs). Application data lives in our own
  Postgres; users are provisioned just-in-time on first authenticated request,
  and each gets a personal organisation. Every tenant query is org-scoped at the
  data layer via `OrgScopedDb`.
- **LLM:** pluggable wrapper, **Groq** free tier by default (`llama-3.1-8b-instant`
  for fast/classification, `llama-3.3-70b-versatile` for drafting). Swap via
  `LLM_PROVIDER`. The wrapper enforces timeouts, retries, structured-output
  validation, and Langfuse tracing.
- **Embeddings:** Groq has no embeddings endpoint yet, so RAG embeddings use a
  separate `EMBEDDING_PROVIDER` (OpenAI by default; `EMBEDDING_DIM=1536`).

## Layout

```
backend/      FastAPI API + Celery worker + shared lib (triage package)
web/          Next.js frontend (design system from the Stitch templates)
db/migrations SQL migrations (forward-only, tracked in schema_migrations)
scripts/      migrate.py — migration runner
evals/        labelled eval sets per LLM feature (added with their modules)
docker-compose.yml   postgres+pgvector, redis, api, worker
```

---

## Prerequisites

- Docker + Docker Compose
- Node.js 20+ (for the frontend)
- Python 3.11+ (only to run `scripts/migrate.py` from the host; optional)
- A free [Supabase](https://supabase.com) project (auth)
- A free [Groq](https://console.groq.com) API key (LLM)

## Setup

1. **Environment**
   ```bash
   cp .env.example .env
   cp web/.env.local.example web/.env.local
   ```
   Fill in: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
   (Supabase → Settings → API), `GROQ_API_KEY`, and a `TOKEN_ENCRYPTION_KEY`:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Mirror the Supabase URL + anon key into `web/.env.local`.

2. **Start the backend stack**
   ```bash
   docker compose up -d --build      # postgres, redis, api, worker
   ```

3. **Apply migrations** (creates all tables + pgvector)
   ```bash
   docker compose exec api python /scripts/migrate.py     # runs inside the stack
   ```
   Or from the host (auto-rewrites the `postgres` host to `localhost`):
   ```bash
   pip install "psycopg[binary]" && python scripts/migrate.py
   ```
   Check status any time with `python scripts/migrate.py --status`.

4. **Run the frontend**
   ```bash
   cd web && npm install && npm run dev
   ```
   Open http://localhost:3000 → sign up → you land on the Triage Queue.

## Verify the foundation

- `GET http://localhost:8000/health` → `{"status":"ok"}`
- `GET http://localhost:8000/health/ready` → postgres + redis `ok`
- In the UI, **Run pipeline self-test** enqueues a `ping` job and polls it to
  `succeeded`, proving API → Redis → worker → Postgres end to end.

## Roadmap (next modules)

2. Mailbox ingestion (Gmail/Graph OAuth + IMAP, dedupe, sanitisation)
3. Classification + evals
4. Knowledge base + RAG
5. Reply drafting (streaming, cited sources)
6. Routing engine (rules → assignee + CRM, Slack notify)
7. Review UI (triage queue, email detail, rules editor)
8. Analytics + audit
9. Hardening & deploy
