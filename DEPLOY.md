# Deployment

The app splits cleanly into a **frontend** (Next.js) and a **backend** (FastAPI
API + Celery worker, with Postgres + Redis). Recommended free-tier hosting:

- **Frontend → Vercel**
- **Backend (API + worker + Postgres + Redis) → Render** (one Blueprint), or
  Railway / Fly.io if you prefer.

---

## 1. Backend on Render (Blueprint)

The repo ships a [`render.yaml`](./render.yaml) that provisions the API, the
Celery worker (with the Beat poller), Redis, and a Postgres 16 database.

1. Push the repo to GitHub.
2. In Render → **New → Blueprint** → pick the repo. Render reads `render.yaml`
   and creates the four resources.
3. Enable **pgvector** on the database: Render → your DB → **Shell** (or any
   `psql`) → `CREATE EXTENSION IF NOT EXISTS vector;` (the migrations also create
   it, but enabling it once is harmless).
4. Set the secret env vars (marked `sync: false`) on **both** the API and worker
   services:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
   - `GROQ_API_KEY`
   - `TOKEN_ENCRYPTION_KEY`
   - `SLACK_WEBHOOK_URL` (optional)
   - `FRONTEND_ORIGIN` = your Vercel URL (for CORS), on the API service
5. **Run migrations** once (Render API service → Shell):
   ```bash
   DATABASE_URL=$DATABASE_URL python -c "import sys; sys.argv=['m']; exec(open('/app/../scripts/migrate.py').read())"
   ```
   …or simpler: add a one-off **Job** / run `python scripts/migrate.py` with
   `DATABASE_URL` set. (Migrations live in `db/migrations`.)

> Free Postgres/Redis instances on Render sleep/expire on a schedule — fine for
> a demo; upgrade the plan for always-on production.

### Railway / Fly.io alternative
- **Railway:** add Postgres + Redis plugins, deploy `backend/` as two services
  (the API `startCommand` and the worker `startCommand` from `render.yaml`).
- **Fly.io:** `fly launch` in `backend/`, add Fly Postgres + Upstash Redis, and
  run the worker as a second process/group.

---

## 2. Frontend on Vercel

1. Vercel → **New Project** → import the repo → set **Root Directory** to `web`.
2. Environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_BASE_URL` = your Render API URL (e.g. `https://triage-api.onrender.com`)
3. Deploy. Update the backend's `FRONTEND_ORIGIN` to the resulting Vercel URL so
   CORS allows it.

> The frontend can also run in Docker via [`web/Dockerfile`](./web/Dockerfile)
> (standalone output) if you'd rather host it alongside the backend.

---

## 3. Post-deploy checklist

- [ ] `GET https://<api>/health` returns `{"status":"ok"}`
- [ ] `GET https://<api>/health/ready` shows postgres + redis `ok`
- [ ] Sign up on the Vercel URL → you reach the triage queue
- [ ] Connect a mailbox in **Settings**; the Beat poller ingests new mail
- [ ] Rotate any secrets that were used during development

## Notes

- **Secrets** live only in the host's environment / a vault — never in the repo
  (`.env` and `web/.env.local` are git-ignored).
- **Scaling:** the worker is stateless; raise `--concurrency` or run more worker
  instances to absorb load. The API is stateless behind the platform's LB.
- **Always-on:** unlike local Docker, hosted workers keep polling mailboxes 24/7.
