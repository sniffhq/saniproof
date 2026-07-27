"""
Audit-facing reporting: a landing page with date-range filters, and CSV
exports for completions (the actual proof-of-clean records) and issues.
These are the artifacts an auditor or client would ask for directly.
"""
import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, Response

from app.auth import staff_required
from app.models import Company, Client, Completion, Issue, TaskAssignment, Shift, MssTask, Zone

reports_bp = Blueprint("reports", __name__)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _default_range():
    end = datetime.utcnow().date()
    start = end - timedelta(days=30)
    return start, end


@reports_bp.route("/company/<uuid:company_id>/reports")
@staff_required
def report_list(company_id):
    company = Company.query.get_or_404(company_id)
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.name).all()

    default_start, default_end = _default_range()
    start = _parse_date(request.args.get("start")) or default_start
    end = _parse_date(request.args.get("end")) or default_end

    return render_template(
        "reports_list.html",
        company=company,
        clients=clients,
        start=start,
        end=end,
        show_sidebar=True,
        active_nav="reports",
    )


def _base_completion_query(company_id, start, end, client_id):
    query = (
        Completion.query.join(TaskAssignment)
        .join(Shift, TaskAssignment.shift_id == Shift.id)
        .join(MssTask, TaskAssignment.mss_task_id == MssTask.id)
        .join(Zone, MssTask.zone_id == Zone.id)
        .filter(Shift.company_id == company_id)
    )
    if start:
        query = query.filter(Completion.completed_at >= start)
    if end:
        query = query.filter(Completion.completed_at < end + timedelta(days=1))
    if client_id:
        query = query.filter(Shift.client_id == client_id)
    return query.order_by(Completion.completed_at.asc())


@reports_bp.route("/company/<uuid:company_id>/reports/completions.csv")
@staff_required
def completions_csv(company_id):
    Company.query.get_or_404(company_id)
    start = _parse_date(request.args.get("start"))
    end = _parse_date(request.args.get("end"))
    client_id = request.args.get("client_id") or None

    completions = _base_completion_query(company_id, start, end, client_id).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Completed at", "Client", "Zone", "Task", "Completed by",
        "Chemical", "Dilution used", "Notes", "Checklist progress",
    ])
    for c in completions:
        assignment = c.task_assignment
        task = assignment.mss_task if assignment else None
        zone = task.zone if task else None
        client = zone.client if zone else None
        checked, total = assignment.checklist_progress() if assignment else (0, 0)
        writer.writerow([
            c.completed_at.strftime("%Y-%m-%d %H:%M") if c.completed_at else "",
            client.name if client else "",
            zone.name if zone else "",
            task.name if task else "",
            c.completed_by_staff.name if c.completed_by_staff else "",
            c.chemical.name if c.chemical else "",
            c.dilution_used or "",
            (c.notes or "").replace("\n", " "),
            f"{checked}/{total}" if total else "",
        ])

    filename = f"saniproof-completions-{datetime.utcnow().date().isoformat()}.csv"
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@reports_bp.route("/company/<uuid:company_id>/reports/issues.csv")
@staff_required
def issues_csv(company_id):
    Company.query.get_or_404(company_id)
    start = _parse_date(request.args.get("start"))
    end = _parse_date(request.args.get("end"))
    status = request.args.get("status") or None

    query = (
        Issue.query.join(TaskAssignment, Issue.task_assignment_id == TaskAssignment.id)
        .join(Shift, TaskAssignment.shift_id == Shift.id)
        .join(MssTask, TaskAssignment.mss_task_id == MssTask.id)
        .join(Zone, MssTask.zone_id == Zone.id)
        .filter(Shift.company_id == company_id)
    )
    if start:
        query = query.filter(Issue.created_at >= start)
    if end:
        query = query.filter(Issue.created_at < end + timedelta(days=1))
    if status:
        query = query.filter(Issue.status == status)
    issues = query.order_by(Issue.created_at.asc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Reported at", "Client", "Zone", "Task", "Severity", "Status",
        "Description", "Reported by", "Corrective action", "Resolved by", "Resolved at",
    ])
    for issue in issues:
        assignment = issue.task_assignment
        task = assignment.mss_task if assignment else None
        zone = task.zone if task else None
        client = zone.client if zone else None
        writer.writerow([
            issue.created_at.strftime("%Y-%m-%d %H:%M") if issue.created_at else "",
            client.name if client else "",
            zone.name if zone else "",
            task.name if task else "",
            issue.severity,
            issue.status,
            (issue.description or "").replace("\n", " "),
            issue.reported_by_staff.name if issue.reported_by_staff else "",
            (issue.corrective_action or "").replace("\n", " "),
            issue.resolved_by_staff.name if issue.resolved_by_staff else "",
            issue.resolved_at.strftime("%Y-%m-%d %H:%M") if issue.resolved_at else "",
        ])

    filename = f"saniproof-issues-{datetime.utcnow().date().isoformat()}.csv"
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
