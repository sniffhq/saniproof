# SaniProof

Flask app for SaniProof, connected to Supabase Postgres (via the Supavisor session pooler — required for IPv4-only hosts like Railway).

## What's here

- `app/models.py` — SQLAlchemy models matching the tables in Supabase (companies, staff, clients, zones, chemicals, mss_tasks, shifts, task_assignments, completions, issues, certifications, sop_documents).
- `app/routes/dashboard.py` — company picker + internal dashboard: today's shifts and task status.
- `app/routes/tasks_admin.py` — browse and create Master Sanitation Schedule tasks.
- `app/routes/sops.py` — SOP document library: view and upload standard operating procedures, link them to tasks.
- `app/routes/clients.py` — list of client food plants, with a link into each one's portal.
- `app/routes/tasks.py` — crew view: open an assigned task, mark it complete with a photo/chemical/notes, or report an issue.
- `app/routes/portal.py` — read-only client portal: a food plant's QA team can see zone-by-zone cleaning status.

## UI structure

Two layouts:
- `base_admin.html` — sidebar nav (Dashboard, Tasks, SOPs, Clients), used for internal company-management pages.
- `base.html` — minimal top bar, used for the company picker, the client-facing portal, and the crew task-execution page (kept lightweight since crews use it on a phone).

## What's NOT here yet (on purpose)

- **No authentication.** Anyone with a URL can view any company/client's data right now. Add login (Flask-Login is the standard fit) before this touches real customer data.
- **No Row Level Security in Supabase.** Intentionally held off until auth is in place — flagged as a TODO.
- **Photo and SOP file uploads save to local disk** (`app/static/uploads`, `app/static/sops`), which is fine for local testing but is NOT persistent on Railway (files vanish on redeploy). Swap for Supabase Storage before this holds anything that matters.
- No edit/delete UI for tasks, SOPs, or clients yet — create-only for now.

## Local setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # then fill in DATABASE_URL with your real Supabase password
python seed.py                 # creates one test company/client/zone/task so you have something to click
python wsgi.py                 # runs at http://localhost:5000
```

## Deploying to Railway

1. Push this folder to a GitHub repo (Railway deploys from GitHub, or via their CLI).
2. Create a new Railway project from that repo.
3. In Railway's project settings, add the environment variables from `.env.example` (`DATABASE_URL`, `SECRET_KEY`) — use your real Supabase **pooler** connection string (Session mode, port 5432) and a real random secret, not the placeholders. The direct connection string (`db.<ref>.supabase.co`) is IPv6-only and will fail to connect from Railway.
4. Railway will detect the `Procfile` and run `gunicorn wsgi:app` automatically.

## Database

Schema lives in Supabase project `lspvfrsjzeorggirtriu` (migrations: `saniproof_initial_schema`, `add_sop_documents`). This app does not create tables itself — it only reads/writes to what's already there. If you change `app/models.py`, you need a matching SQL migration in Supabase or they'll drift out of sync.
