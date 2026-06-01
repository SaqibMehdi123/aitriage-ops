# AI Inbox Triage + Reply Router

An AI-powered system that turns a shared support/sales inbox into a calm,
triaged queue. It connects to a mailbox, **classifies every incoming email by
intent**, **drafts a context-aware reply grounded in your own knowledge base**,
**routes it to the right person**, and presents it in a clean review UI where a
human edits and sends with one click.

Small teams lose hours sorting email and writing near-identical replies. This
keeps a human in control of what gets sent while doing the repetitive triage and
drafting automatically — cutting first-response time from minutes to seconds.

`Next.js` · `FastAPI` · `PostgreSQL + pgvector` · `Redis` · `Celery` · `Groq LLM` · `Supabase Auth` · `Docker`

---

## Features

- **Intent classification** — every email is tagged with a category, urgency,
  and a confidence score. Low-confidence emails are routed to a human lane
  rather than guessed.
- **Knowledge-grounded replies (RAG)** — upload your FAQs, policies, and canned
  answers; the assistant retrieves the relevant passages and drafts replies
  grounded in them, with the sources cited.
- **Streaming drafts** — replies are generated token-by-token in the editor, so
  agents see the answer compose in real time and can edit before sending.
- **Rules-based routing** — a visual IF/THEN builder assigns emails to the right
  teammate by category, urgency, or keyword, with optional CRM logging.
- **Review-and-send UI** — a triage queue and a two-pane email view with the
  conversation alongside an editable AI draft and its citations.
- **Slack notifications** — the right people get pinged the moment an important
  email is routed.
- **Analytics & audit** — volume, category mix, median response time, hours
  saved, and draft-acceptance rate, plus a full audit trail of every action.
- **Multi-tenant & secure** — organisation-scoped data isolation, encrypted
  mailbox credentials, and prompt-injection defenses on untrusted email content.

## How it works

```
   Mailbox (Gmail / Outlook / IMAP)
        │  new message (poll or webhook)
        ▼
   Ingest ──► Classify ──► Route ──┬──► Slack notify
   (dedupe,   (intent +    (rules →│
   sanitise)  confidence)  assignee)
                   └──► Draft reply (retrieves knowledge base, streams to UI)
        │
        ▼
   Review queue → agent edits the draft → one-click Send
```

Long-running work (classification, embedding, drafting, routing, mailbox sync)
runs on background workers off the request path, so the UI stays instant and the
system absorbs morning email bursts.

## Architecture

```
Next.js (App Router, TypeScript, Tailwind)        ← review UI
        │  authenticated API calls
        ▼
FastAPI (Python)  ──enqueue──▶  Redis  ──▶  Celery workers
        │                                        │
        └──────────────┬─────────────────────────┘
                       ▼
        PostgreSQL + pgvector  (emails, drafts, classifications,
                                routing rules, knowledge, audit log)
```

- **AI** runs through a single provider-agnostic wrapper with retries, timeouts,
  structured-output validation, and tracing.
- **Retrieval** uses pgvector for semantic search over the knowledge base — one
  database for both relational data and embeddings.
- **Auth** is handled by Supabase; every database query is scoped to the
  caller's organisation at the data layer.

---

## Getting started

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- A free [Supabase](https://supabase.com) project (authentication)
- A free [Groq](https://console.groq.com) API key (LLM)

### 1. Configure environment
```bash
cp .env.example .env
cp web/.env.local.example web/.env.local
```
Fill in your Supabase keys, Groq API key, and a generated encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Start the backend
```bash
docker compose up -d --build
docker compose exec api python /scripts/migrate.py
```

### 3. Start the frontend
```bash
cd web && npm install && npm run dev
```
Open http://localhost:3000, create an account, and you're in the triage queue.

### Connect a mailbox
In **Settings → Connect a mailbox**, add a Gmail address with an
[app password](https://myaccount.google.com/apppasswords) (host `imap.gmail.com`,
port `993`). New mail is then ingested automatically; credentials are encrypted
at rest.

---

## Tech stack

| Layer | Choice |
|------|--------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, Celery, Redis |
| Database | PostgreSQL + pgvector |
| AI | Groq (LLM) · pluggable embeddings |
| Auth | Supabase |
| Infra | Docker Compose |

## Project structure

```
backend/      FastAPI API, Celery workers, and the core services
              (ingestion, classification, knowledge/RAG, drafting, routing)
web/          Next.js review UI
db/           database migrations
evals/        labelled evaluation sets for the AI features
```

---

## License

MIT
