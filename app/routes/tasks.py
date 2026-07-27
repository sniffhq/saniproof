"""
Crew-facing task execution: view an assigned task and mark it complete
with a photo, the chemical used, and notes. This is the mobile-web flow
crews would use on a phone during a shift.

Requires a logged-in Staff account (any role) belonging to the same
company as the task -- see _check_company_access below. This used to be
open to anyone with the URL; now that accounts exist, that's closed.

Photo storage here is a local-disk stub (app/static/uploads) so the
scaffold runs without extra setup. Swap this for Supabase Storage (or S3)
before real crews start uploading real photos -- local disk on Railway
is NOT persistent across deploys.
"""
import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import TaskAssignment, Chemical, Completion, Issue, Staff

tasks_bp = Blueprint("tasks", __name__)


def _check_company_access(assignment):
    if not isinstance(current_user, Staff) or current_user.company_id != assignment.shift.company_id:
        abort(403)


@tasks_bp.route("/task-assignment/<uuid:assignment_id>")
@login_required
def task_detail(assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    _check_company_access(assignment)
    chemicals = Chemical.query.filter_by(
        company_id=assignment.shift.company_id
    ).all()
    return render_template("task_detail.html", assignment=assignment, chemicals=chemicals)


@tasks_bp.route("/task-assignment/<uuid:assignment_id>/complete", methods=["POST"])
@login_required
def complete_task(assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    _check_company_access(assignment)

    photo_url = None
    photo = request.files.get("photo")
    if photo and photo.filename:
        filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
        photo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
        photo_url = f"/static/uploads/{filename}"

    completion = Completion(
        task_assignment_id=assignment.id,
        completed_by=current_user.id,
        photo_url=photo_url,
        chemical_id=request.form.get("chemical_id") or None,
        dilution_used=request.form.get("dilution_used"),
        notes=request.form.get("notes"),
    )
    db.session.add(completion)
    assignment.status = "completed"
    db.session.commit()

    return redirect(url_for("tasks.task_detail", assignment_id=assignment.id))


@tasks_bp.route("/task-assignment/<uuid:assignment_id>/report-issue", methods=["POST"])
@login_required
def report_issue(assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    _check_company_access(assignment)

    issue = Issue(
        task_assignment_id=assignment.id,
        reported_by=current_user.id,
        description=request.form.get("description", ""),
        severity=request.form.get("severity", "medium"),
    )
    db.session.add(issue)
    db.session.commit()

    return redirect(url_for("tasks.task_detail", assignment_id=assignment.id))
