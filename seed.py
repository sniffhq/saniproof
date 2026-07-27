"""
Quick one-off script to populate a company/client/zone/task/shift so you
have something to click through immediately.

Run with:  python seed.py
Safe to run multiple times against a fresh Supabase project; not
idempotent (will create duplicates if you re-run it against data that's
already there).
"""
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Company, Staff, Client, Zone, Chemical, MssTask, Shift, TaskAssignment

app = create_app()

with app.app_context():
    company = Company(name="Compeer Contract Cleaning Services")
    db.session.add(company)
    db.session.flush()

    staff = Staff(company_id=company.id, name="Test Admin", email="admin@example.com", role="admin")
    staff.set_password("changeme123")
    db.session.add(staff)

    client = Client(company_id=company.id, name="Acme Food Processing Plant")
    db.session.add(client)
    db.session.flush()

    zone = Zone(client_id=client.id, name="Production Floor - Line 1")
    db.session.add(zone)
    db.session.flush()

    chemical = Chemical(company_id=company.id, name="Quat Sanitizer", default_dilution="1:64")
    db.session.add(chemical)
    db.session.flush()

    task = MssTask(
        zone_id=zone.id,
        name="Sanitize conveyor belt",
        description="Full teardown, wash, rinse, sanitize per SOP-014",
        frequency="daily",
        default_chemical_id=chemical.id,
    )
    db.session.add(task)
    db.session.flush()

    shift = Shift(company_id=company.id, client_id=client.id, shift_date=date.today())
    db.session.add(shift)
    db.session.flush()

    assignment = TaskAssignment(mss_task_id=task.id, shift_id=shift.id, assigned_staff_id=staff.id)
    db.session.add(assignment)

    db.session.commit()

    print(f"Log in at /login with admin@example.com / changeme123")
    print(f"Company dashboard: /company/{company.id}")
    print(f"Task detail:       /task-assignment/{assignment.id}")
    print(f"Client portal:     /portal/{client.id} (no login yet -- create a portal account via Users)")
