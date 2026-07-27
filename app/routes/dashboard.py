"""
Internal dashboard for sanitation company staff (admin/crew).

NOTE: there is no authentication wired up yet -- this is a scaffold.
Right now anyone hitting these routes can pick any company/shift. Before
real customer data goes anywhere near this, add login (e.g. Flask-Login)
and enable Supabase Row Level Security as discussed.
"""
from datetime import date

from flask import Blueprint, render_template, abort

from app.extensions import db
from app.models import Company, Shift, TaskAssignment

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    companies = Company.query.order_by(Company.name).all()
    return render_template("index.html", companies=companies)


@dashboard_bp.route("/company/<uuid:company_id>")
def company_dashboard(company_id):
    company = Company.query.get_or_404(company_id)

    today_shifts = (
        Shift.query.filter_by(company_id=company_id, shift_date=date.today())
        .order_by(Shift.start_time)
        .all()
    )

    shift_ids = [s.id for s in today_shifts]
    assignments = (
        TaskAssignment.query.filter(TaskAssignment.shift_id.in_(shift_ids)).all()
        if shift_ids
        else []
    )

    counts = {"pending": 0, "in_progress": 0, "completed": 0, "skipped": 0}
    for a in assignments:
        counts[a.status] = counts.get(a.status, 0) + 1

    return render_template(
        "dashboard.html",
        company=company,
        shifts=today_shifts,
        assignments=assignments,
        counts=counts,
        show_sidebar=True,
        active_nav="dashboard",
    )
