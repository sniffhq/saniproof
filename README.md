# SaniProof

Flask app for SaniProof, connected to Supabase Postgres (via the Supavisor session pooler — required for IPv4-only hosts like Railway).

## What's here

- `app/models.py` — SQLAlchemy models matching the tables in Supabase (companies, staff, clients, zones, chemicals, mss_tasks, shifts, task_assignments, completions, issues, certifications, sop_documents, client_user_assignments).
- `app/auth.py` — Flask-Login setup: two login-capable models (`Staff`, `ClientUser`) sharing one login form, plus `staff_required` / `client_user_required` decorators that enforce ownership (a staff account can only see its own company; a client user can only see clients it's been assigned).
- `app/routes/auth.py` — login/logout.
- `app/routes/dashboard.py` — internal dashboard: today's shifts and task status.
- `app/routes/tasks_admin.py` — browse and create Master Sanitation Schedule tasks, and build each task's checklist template (the steps a crew checks off).
- `app/routes/sops.py` — SOP document library: view and upload standard operating procedures, link them to tasks.
- `app/routes/clients.py` — list clients, create a new client, add zones to it.
- `app/routes/users_admin.py` — create staff accounts and client-portal accounts, and assign a portal account to one or more clients.
- `app/routes/tasks.py` — crew view: open an assigned task, check off checklist steps in real time (with per-step notes), mark it complete with a photo/chemical/notes, or report an issue. Requires a staff login.
- `app/routes/portal.py` — read-only client portal: a food plant's QA team sees zone-by-zone cleaning status. Requires a client-portal login, scoped to assigned clients.

## Accounts & access model

Two separate account types, one login form (`/login`):

- **Staff** (`staff` table) — belongs to one company, full access to that company's dashboard, tasks, SOPs, clients, and user management. Roles (`admin`/`crew`) exist in the schema but aren't enforced differently yet — both get the same access for now.
- **Client portal users** (`client_users` table) — not tied to a company; instead assigned to one or more specific clients via `client_user_assignments`. Only see the portal(s) for clients they've been assigned. A user assigned to more than one facility gets a picker at `/portal/select`.

New accounts are created from the **Users** page in the sidebar — there's no self-signup. To create the very first staff login for a new company, set a password directly in Supabase (see "Bootstrapping" below).

## UI structure

Two layouts:
- `base_admin.html` — sidebar nav (Dashboard, Tasks, SOPs, Clients, Users), used for internal company-management pages.
- `base.html` — minimal top bar, used for login, the client-facing portal, and the crew task-execution page (kept lightweight since crews use it on a phone).

## Checklists

Each task (`mss_tasks`) can have a checklist template (`checklist_items`) defined once by an admin from the task's detail page (Tasks -> click a task). During execution, a crew member checks items off and can leave a note per step on the task's mobile page (`checklist_responses`); each check/uncheck and note saves immediately via a small AJAX call, no page reload, with a live progress bar. Checking any item bumps a `pending` assignment to `in_progress` automatically. Finishing the checklist does **not** auto-complete the task -- "mark complete" (photo + chemical + notes) is still a separate, explicit step, since that's the actual proof-of-clean record. A task with no checklist items defined just skips straight to the mark-complete form, same as before.

## What's NOT here yet (on purpose)

- **No Row Level Security in Supabase.** App-level checks (`staff_required`, `client_user_required`) enforce access now, but RLS as a second layer in the database itself is still a TODO.
- **Photo and SOP file uploads save to local disk** (`app/static/uploads`, `app/static/sops`), which is fine for local testing but is NOT persistent on Railway (files vanish on redeploy). Swap for Supabase Storage before this holds anything that matters.
- No edit/delete/reorder UI for tasks, checklist items, SOPs, clients, or user accounts yet — create-only for now.
- No password reset flow — an admin has to reset a forgotten password directly in Supabase for now.
- Staff `admin` vs `crew` role doesn't yet restrict anything differently.

## Local setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # then fill in DATABASE_URL with your real Supabase password
python seed.py                 # creates a test company + admin login (admin@example.com / changeme123)
python wsgi.py                 # runs at http://localhost:5000
```

## Bootstrapping a first login on an existing company

If a company already has staff rows without a password (e.g. seeded directly via SQL), generate a hash and set it:

```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

Then `update staff set password_hash = '<hash>' where email = '...'` in Supabase's SQL editor. After that, use the Users page to create everyone else properly.

## Deploying to Railway

1. Push this folder to a GitHub repo (Railway deploys from GitHub, or via their CLI).
2. Create a new Railway project from that repo.
3. In Railway's project settings, add the environment variables from `.env.example` (`DATABASE_URL`, `SECRET_KEY`) — use your real Supabase **pooler** connection string (Session mode, port 5432) and a real random secret, not the placeholders. The direct connection string (`db.<ref>.supabase.co`) is IPv6-only and will fail to connect from Railway.
4. Railway will detect the `Procfile` and run `gunicorn wsgi:app` automatically.

## Database

Schema lives in Supabase project `lspvfrsjzeorggirtriu` (migrations: `saniproof_initial_schema`, `add_sop_documents`, `add_auth_and_client_assignments`, `add_checklists`). This app does not create tables itself — it only reads/writes to what's already there. If you change `app/models.py`, you need a matching SQL migration in Supabase or they'll drift out of sync.
