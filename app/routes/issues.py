"""
Issue resolution: view every issue a crew has flagged across the company
(open or resolved), and close one out with a corrective action. The
database already modeled resolved_by/resolved_at/corrective_action --
this is the UI that was missing to actually use them.
"""
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Issue, TaskAssignment, Shift

issues_bp = Blueprint("issues", __name__)


@issues_bp.route("/company/<uuid:company_id>/issues")
@staff_required
def issue_list(company_id):
    company = Company.query.get_or_404(company_id)

    status_filter = request.args.get("status", "open")
    query = (
        Issue.query.join(TaskAssignment).join(Shift)
        .filter(Shift.company_id == company_id)
    )
    if status_filter in ("open", "resolved"):
        query = query.filter(Issue.status == status_filter)

    issues = query.order_by(Issue.created_at.desc()).all()

    return render_template(
        "issues_list.html",
        company=company,
        issues=issues,
        status_filter=status_filter,
        show_sidebar=True,
        active_nav="issues",
    )


@issues_bp.route("/company/<uuid:company_id>/issues/<uuid:issue_id>")
@staff_required
def issue_detail(company_id, issue_id):
    company = Company.query.get_or_404(company_id)
    issue = (
        Issue.query.join(TaskAssignment).join(Shift)
        .filter(Issue.id == issue_id, Shift.company_id == company_id)
        .first_or_404()
    )

    return render_template(
        "issue_detail.html", company=company, issue=issue, show_sidebar=True, active_nav="issues"
    )


@issues_bp.route("/company/<uuid:company_id>/issues/<uuid:issue_id>/resolve", methods=["POST"])
@staff_required
def issue_resolve(company_id, issue_id):
    issue = (
        Issue.query.join(TaskAssignment).join(Shift)
        .filter(Issue.id == issue_id, Shift.company_id == company_id)
        .first_or_404()
    )

    issue.corrective_action = request.form.get("corrective_action", "")
    issue.status = "resolved"
    issue.resolved_by = current_user.id
    issue.resolved_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Issue marked resolved.")
    return redirect(url_for("issues.issue_list", company_id=company_id))
