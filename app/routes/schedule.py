"""
Scheduling: create shifts for a client on a given date, and assign that
client's active tasks to a shift (optionally to a specific crew member).

This is the piece that was previously SQL/seed-script-only -- without it
there was no way to actually put a new client on the calendar through
the UI.
"""
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Client, Zone, MssTask, Shift, TaskAssignment, Staff

schedule_bp = Blueprint("schedule", __name__)


def _get_company_shift_or_404(company_id, shift_id):
    return Shift.query.filter_by(id=shift_id, company_id=company_id).first_or_404()


@schedule_bp.route("/company/<uuid:company_id>/schedule")
@staff_required
def schedule_list(company_id):
    company = Company.query.get_or_404(company_id)
    shifts = (
        Shift.query.filter_by(company_id=company_id)
        .order_by(Shift.shift_date.desc())
        .limit(50)
        .all()
    )
    return render_template(
        "schedule_list.html", company=company, shifts=shifts, show_sidebar=True, active_nav="schedule"
    )


@schedule_bp.route("/company/<uuid:company_id>/schedule/new", methods=["GET", "POST"])
@staff_required
def shift_new(company_id):
    company = Company.query.get_or_404(company_id)
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.name).all()

    if request.method == "POST":
        shift = Shift(
            company_id=company_id,
            client_id=request.form["client_id"],
            shift_date=request.form["shift_date"],
        )
        db.session.add(shift)
        db.session.commit()
        flash("Shift created. Now add tasks to it below.")
        return redirect(url_for("schedule.shift_detail", company_id=company_id, shift_id=shift.id))

    return render_template(
        "shift_form.html",
        company=company,
        clients=clients,
        today=date.today().isoformat(),
        show_sidebar=True,
        active_nav="schedule",
    )


@schedule_bp.route("/company/<uuid:company_id>/schedule/<uuid:shift_id>")
@staff_required
def shift_detail(company_id, shift_id):
    company = Company.query.get_or_404(company_id)
    shift = _get_company_shift_or_404(company_id, shift_id)

    assigned_task_ids = {a.mss_task_id for a in shift.assignments}
    available_tasks = (
        MssTask.query.join(Zone)
        .filter(Zone.client_id == shift.client_id, MssTask.active == True)  # noqa: E712
        .order_by(Zone.name, MssTask.name)
        .all()
    )
    available_tasks = [t for t in available_tasks if t.id not in assigned_task_ids]

    staff = Staff.query.filter_by(company_id=company_id, active=True).order_by(Staff.name).all()

    return render_template(
        "shift_detail.html",
        company=company,
        shift=shift,
        available_tasks=available_tasks,
        staff=staff,
        show_sidebar=True,
        active_nav="schedule",
    )


@schedule_bp.route("/company/<uuid:company_id>/schedule/<uuid:shift_id>/assign", methods=["POST"])
@staff_required
def shift_assign(company_id, shift_id):
    shift = _get_company_shift_or_404(company_id, shift_id)

    task_ids = request.form.getlist("task_ids")
    added = 0
    for task_id in task_ids:
        # Confirm the task actually belongs to this shift's client before
        # attaching it -- prevents assigning an unrelated client's task by
        # tampering with the submitted form.
        task = (
            MssTask.query.join(Zone)
            .filter(MssTask.id == task_id, Zone.client_id == shift.client_id)
            .first()
        )
        if not task:
            continue

        staff_id = request.form.get(f"staff_{task_id}") or None
        assignment = TaskAssignment(mss_task_id=task.id, shift_id=shift.id, assigned_staff_id=staff_id)
        db.session.add(assignment)
        added += 1

    db.session.commit()
    flash(f"Added {added} task{'s' if added != 1 else ''} to the shift.")
    return redirect(url_for("schedule.shift_detail", company_id=company_id, shift_id=shift_id))
