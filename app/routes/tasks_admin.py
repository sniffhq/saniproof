"""
Admin-side task management: browse the full task list for a company and
create new recurring sanitation tasks (Master Sanitation Schedule entries).

This is distinct from app/routes/tasks.py, which handles a crew member
executing a single already-assigned task (marking it complete, reporting
an issue). This file is about defining/maintaining the schedule itself.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Client, Zone, Chemical, MssTask, SopDocument, ChecklistItem

tasks_admin_bp = Blueprint("tasks_admin", __name__)


def _get_company_task_or_404(company_id, task_id):
    """Fetch a task, confirming it belongs (via zone -> client) to this
    company -- prevents a staff member from managing another company's
    task by guessing a task_id."""
    return (
        MssTask.query.join(Zone).join(Client)
        .filter(MssTask.id == task_id, Client.company_id == company_id)
        .first_or_404()
    )


@tasks_admin_bp.route("/company/<uuid:company_id>/tasks")
@staff_required
def task_list(company_id):
    company = Company.query.get_or_404(company_id)

    tasks = (
        MssTask.query.join(Zone).join(Client).filter(Client.company_id == company_id)
        .order_by(Client.name, Zone.name, MssTask.name)
        .all()
    )

    return render_template(
        "tasks_list.html", company=company, tasks=tasks, show_sidebar=True, active_nav="tasks"
    )


@tasks_admin_bp.route("/company/<uuid:company_id>/tasks/new", methods=["GET", "POST"])
@staff_required
def task_new(company_id):
    company = Company.query.get_or_404(company_id)

    zones = (
        Zone.query.join(Client).filter(Client.company_id == company_id)
        .order_by(Client.name, Zone.name)
        .all()
    )
    chemicals = Chemical.query.filter_by(company_id=company_id).order_by(Chemical.name).all()
    sops = SopDocument.query.filter_by(company_id=company_id).order_by(SopDocument.title).all()

    if request.method == "POST":
        task = MssTask(
            zone_id=request.form["zone_id"],
            name=request.form["name"],
            description=request.form.get("description"),
            frequency=request.form["frequency"],
            default_chemical_id=request.form.get("default_chemical_id") or None,
            sop_document_id=request.form.get("sop_document_id") or None,
        )
        db.session.add(task)
        db.session.commit()
        flash(f'Task "{task.name}" created. Now build its checklist below.')
        return redirect(url_for("tasks_admin.task_detail", company_id=company_id, task_id=task.id))

    return render_template(
        "task_form.html",
        company=company,
        zones=zones,
        chemicals=chemicals,
        sops=sops,
        show_sidebar=True,
        active_nav="tasks",
    )


@tasks_admin_bp.route("/company/<uuid:company_id>/tasks/<uuid:task_id>")
@staff_required
def task_detail(company_id, task_id):
    company = Company.query.get_or_404(company_id)
    task = _get_company_task_or_404(company_id, task_id)

    return render_template(
        "task_admin_detail.html",
        company=company,
        task=task,
        show_sidebar=True,
        active_nav="tasks",
    )


@tasks_admin_bp.route("/company/<uuid:company_id>/tasks/<uuid:task_id>/checklist-items/new", methods=["POST"])
@staff_required
def checklist_item_new(company_id, task_id):
    task = _get_company_task_or_404(company_id, task_id)

    next_order = len(task.checklist_items)
    item = ChecklistItem(
        mss_task_id=task.id,
        label=request.form["label"],
        sort_order=next_order,
    )
    db.session.add(item)
    db.session.commit()
    flash(f'Checklist step "{item.label}" added.')
    return redirect(url_for("tasks_admin.task_detail", company_id=company_id, task_id=task_id))
