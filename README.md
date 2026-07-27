# SaniProof

Flask scaffold for SaniProof, connected to Supabase Postgres.

## What's here

- `app/models.py` — SQLAlchemy models matching the tables already created in Supabase (companies, staff, clients, zones, chemicals, mss_tasks, shifts, task_assignments, completions, issues, certifications).
- `app/routes/dashboard.py` — internal dashboard: pick a company, see today's shifts and task status.
- `app/routes/tasks.py` — crew view: open an assigned task, mark it complete with a photo/chemical/notes, or report an issue.
- `app/routes/portal.py` — read-only client portal: a food plant's QA team can see zone-by-zone cleaning status.

## What's NOT here yet (on purpose, for a first scaffold)

- **No authentication.** Anyone with a URL can view any company/client's data right now. Add login (Flask-Login is the standard fit) before this touches real customer data.
- **No Row Level Security in Supabase.** Was intentionally held off until the app is far enough along to test against it — flagged as a TODO.
- **Photo uploads save to local disk** (`app/static/uploads`), which is fine for local testing but is NOT persistent on Railway (files vanish on redeploy). Swap for Supabase Storage before crews start uploading real photos.
- No way to create companies/clients/zones/tasks through the UI yet — use the `seed.py` script or Supabase's table editor directly.

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
3. In Railway's project settings, add the environment variables from `.env.example` (`DATABASE_URL`, `SECRET_KEY`) — use your real Supabase connection string and a real random secret, not the placeholders.
4. Railway will detect the `Procfile` and run `gunicorn wsgi:app` automatically.

## Database

Schema already lives in Supabase project `lspvfrsjzeorggirtriu` (migration: `saniproof_initial_schema`). This app does not create tables itself — it only reads/writes to what's already there. If you change `app/models.py`, you need a matching SQL migration in Supabase or they'll drift out of sync.
