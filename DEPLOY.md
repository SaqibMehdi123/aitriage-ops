# Deployment — Render (backend) + Netlify (frontend), free tier

- **Backend** (API + Celery worker + Beat + Postgres + Redis) → **Render**, all in
  the free tier, via the [`render.yaml`](./render.yaml) Blueprint.
- **Frontend** (Next.js) → **Netlify**, free tier, via [`netlify.toml`](./netlify.toml).

### Free-tier caveats (fine for a demo, know them going in)
- Render's free web service **sleeps after ~15 min idle** → ~30–60s cold start on
  the next request, and **mailbox polling pauses while asleep**.
- Render's **free Postgres is deleted after ~30 days** (re-create when needed).
- Render's free tier has **no separate worker service**, so the worker + Beat run
  *inside* the API web service (handled by the Blueprint's start command).

---

## 1. Backend on Render

1. Push the repo to GitHub (already done).
2. Render → **New → Blueprint** → select the repo. Render reads `render.yaml` and
   creates: the **triage-api** web service, a **Postgres** db, and a **Key Value**
   (Redis) instance.
3. On the **triage-api** service → **Environment**, fill the secret vars:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
   - `GROQ_API_KEY`
   - `TOKEN_ENCRYPTION_KEY`
   - `SLACK_WEBHOOK_URL` (optional), `CRM_PROVIDER` / `CRM_WEBHOOK_URL` / `HUBSPOT_TOKEN` (optional)
   - `FRONTEND_ORIGIN` → set this to your Netlify URL once you have it (step 2 below)
   `DATABASE_URL` and `REDIS_URL` are wired automatically by the Blueprint.
4. Deploy. On boot it runs the DB migrations, starts the worker+Beat, then the API.
   - If the `vector` extension isn't created automatically, open the DB's **psql**
     shell once and run `CREATE EXTENSION IF NOT EXISTS vector;`
5. Verify: `https://triage-api-XXXX.onrender.com/health` → `{"status":"ok"}`.
   Note this base URL for the frontend.

## 2. Frontend on Netlify

1. Netlify → **Add new site → Import an existing project** → select the repo.
   Netlify reads `netlify.toml` (base directory `web`) and auto-installs the
   Next.js plugin.
2. Set environment variables (Site settings → Environment):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_BASE_URL` = your Render API URL from step 1.5
3. Deploy → you get a URL like `https://your-site.netlify.app`.

## 3. Connect the two

1. Back on **Render → triage-api → Environment**, set `FRONTEND_ORIGIN` to the
   Netlify URL (this is the CORS allow-origin) and let it redeploy.
2. In **Supabase → Authentication → URL Configuration**, add the Netlify URL to
   **Site URL** / redirect allow-list.

## 4. Post-deploy checklist

- [ ] `GET https://<render-api>/health` → ok; `/health/ready` → postgres + redis ok
- [ ] Sign up on the Netlify URL → reach the triage queue
- [ ] Settings → connect a mailbox (the poller runs while the service is awake)
- [ ] Open an email → Generate → Send (delivers via SMTP)

## Notes / alternatives
- For an **always-on** backend (no sleep) and persistent Postgres, upgrade the
  Render services off free, or split the worker onto a paid Background Worker.
- The frontend can alternatively deploy to **Vercel** (set root dir to `web`,
  same env vars) — `output: standalone` is disabled outside Docker so either host
  builds natively.
- `web/Dockerfile` + the `triage-api` image also let you self-host on Fly.io etc.
