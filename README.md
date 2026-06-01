# AI Inbox Triage + Reply Router

An event-driven pipeline with **human-in-the-loop review** that turns a shared
support/sales inbox into a triaged, auto-drafted queue. It connects to a
mailbox, **classifies** every incoming email by intent, **drafts a context-aware
reply grounded in your own knowledge base** (RAG), **routes** it to the right
person, and surfaces it in a review UI where a human edits and sends with one
click.

> Built to run **100% free**: Groq for the LLM, an offline embedder for RAG, and
> your own Postgres — no paid API required.

---

## What it does

```
                      ┌─────────────────────────────────────────────┐
   Mailbox (IMAP/      │  Ingest → Classify → Route ┬─► Slack notify  │
   Gmail/Graph)  ──►   │  (dedupe,   (Groq,    (rules │                │
   poll / webhook      │  sanitise) confidence) →assignee)            │
                      │              └─► Draft reply (RAG over KB, streamed) │
                      └───────────────────────┬─────────────────────┘
                                              ▼
                         Review UI: triage queue · email detail ·
                         editable streaming draft + citations ·
                         one-click Send / Send & log to CRM
```

- **Ingestion** — Gmail/Microsoft Graph (OAuth) or IMAP (app password). Dedupes
  by message-id, strips HTML + neutralises prompt-injection, polls every 60s.
- **Classification** — structured-output `{category, confidence, urgency}` via
  the Groq wrapper; below a confidence threshold it routes to a human lane
  instead of guessing. Ships with a labelled eval set (≥90% target).
- **Knowledge base + RAG** — upload docs → chunk → embed into pgvector →
  top-k retrieval (org-scoped) to ground drafts and cite sources.
- **Drafting** — composes a reply from the thread + retrieved knowledge,
  **streams token-by-token** to the UI, records cited sources.
- **Routing** — ordered IF/THEN rules → assignee + CRM action, with optional
  **Slack** notification.
- **Review UI** — triage queue, two-pane email detail with an editable draft,
  rules editor, knowledge base, and an analytics dashboard.
- **Analytics + audit** — volume, category mix, median response time, hours
  saved, draft-acceptance rate, and a full audit log.

Every email is multi-tenant **org-scoped** at the data layer, and every action
is written to an audit log.

## Screens

Triage Queue · Email Detail (streaming AI draft + citations) · Routing Rules
(visual IF/THEN builder) · Knowledge Base · Analytics · Settings (connect
mailbox). Design system: "Precision Operations" (violet, Geist).

---

## Architecture

```
Next.js (App Router, TS, Tailwind)        ← review UI + thin reads
        │  Authorization: Bearer <Supabase JWT>
        ▼
FastAPI (Python)  ──enqueue──▶  Redis  ──▶  Celery workers (+ Beat poller)
        │                                        │
        └──────────────┬─────────────────────────┘
                       ▼
        PostgreSQL + pgvector  (emails, drafts, classifications,
                                routing rules, knowledge, jobs, audit log)
```

- **Auth/identity:** Supabase (verifies asymmetric **JWKS** tokens, HS256
  fallback). Users are JIT-provisioned with a personal organisation; every
  tenant query is org-scoped via `OrgScopedDb`.
- **LLM:** pluggable wrapper, **Groq** by default (`llama-3.1-8b-instant` for
  classification, `llama-3.3-70b-versatile` for drafting) with retries,
  timeouts, structured-output validation, and Langfuse tracing.
- **Embeddings:** pluggable — `hash` (free, offline, default), `fastembed`
  (free local), or `openai`. Default vector dim 384.

## Tech stack

Next.js 15 · React 19 · TypeScript · Tailwind · Recharts · FastAPI · Celery ·
Redis · PostgreSQL + pgvector · Supabase Auth · Groq · Docker Compose.

---

## Quick start

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- A free [Supabase](https://supabase.com) project (auth)
- A free [Groq](https://console.groq.com) API key (LLM)

### 1. Environment
```bash
cp .env.example .env
cp web/.env.local.example web/.env.local
```
Fill in `.env`:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` (Supabase → Settings → API)
- `GROQ_API_KEY`
- `TOKEN_ENCRYPTION_KEY` — generate with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- *(optional)* `SLACK_WEBHOOK_URL` for routing notifications

Mirror `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` into `web/.env.local`.

### 2. Start the backend
```bash
docker compose up -d --build           # postgres, redis, api, worker(+beat)
docker compose exec api python /scripts/migrate.py   # apply migrations
```

### 3. Start the frontend
```bash
cd web && npm install && npm run dev
```
Open http://localhost:3000 → sign up → you land on the Triage Queue.

### 4. Try it
- On the queue, click **Seed demo emails** to push sample emails through the
  full pipeline, or
- Go to **Settings → Connect a mailbox** to wire a real inbox (see below).

---

## Connecting a real mailbox (Gmail via IMAP)

1. Enable **2-Step Verification** on your Google account.
2. Enable **IMAP** in Gmail → Settings → Forwarding and POP/IMAP.
3. Create a 16-character **App Password**: https://myaccount.google.com/apppasswords
4. In the app: **Settings → Connect a mailbox** → host `imap.gmail.com`,
   port `993`, your address, the app password → **Connect**.

The initial sync pulls recent mail; the Beat poller then ingests new mail every
60 seconds. Credentials are encrypted at rest (Fernet).

> "Always on" applies while the stack is running. For 24/7, deploy the backend
> to an always-on host (see roadmap).

---

## Project structure

```
backend/      FastAPI API + Celery worker + the `triage` package
  triage/
    api/            routers (emails, accounts, knowledge, rules, analytics, …)
    classification/ structured-output intent classification + threshold routing
    drafting/       RAG-grounded reply generation (+ streaming)
    knowledge/      chunking, pluggable embeddings, pgvector retrieval
    routing/        rule engine + Slack/CRM notify
    ingestion/      Gmail/Graph/IMAP connectors, sanitiser, dedupe, sync
    llm/            provider-agnostic LLM wrapper (Groq)
web/          Next.js frontend (the review UI)
db/migrations SQL migrations (forward-only)
evals/        labelled eval sets per LLM feature
```

## Tests

```bash
docker compose exec api pytest          # unit + DB integration tests
docker compose exec api python /evals/classification/run_eval.py   # eval set
```

---

## Module status

| # | Module | Status |
|---|--------|--------|
| 0 | Foundation (Docker, DB, Redis, LLM wrapper, jobs) | ✅ |
| 1 | Auth & multi-tenancy | ✅ |
| 2 | Mailbox ingestion (Gmail/Graph/IMAP, dedupe, sanitise, poller) | ✅ |
| 3 | Classification + evals | ✅ |
| 4 | Knowledge base + RAG | ✅ |
| 5 | Reply drafting (streaming, citations) | ✅ |
| 6 | Routing engine (rules → assignee + CRM, Slack) | ✅ |
| 7 | Review UI | ✅ |
| 8 | Analytics + audit | ✅ |
| 9 | Hardening & deploy (rate limits, DLQ, PII redaction, retention, deploy) | ⏳ |

### Known follow-ups
- **Outbound send** currently records the human's send decision (audit + metrics)
  but does not yet transmit the reply via the provider.
- **CRM logging** records intent; a real HubSpot/CRM integration is optional
  (a "Should", not a "Must").

---

## License

Portfolio project.
