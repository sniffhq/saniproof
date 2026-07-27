"""
Read-only client portal: lets a food plant's QA team see cleaning
status and completion history without calling the sanitation company.

Protected by client_user_required (see app/auth.py): a logged-in
ClientUser can only view portals for clients they've been explicitly
assigned to.
"""
from flask import Blueprint, render_template
from flask_login import current_user

from app.auth import client_user_required
from app.models import Client, Zone, MssTask, TaskAssignment, Completion

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/portal/select")
@client_user_required
def client_select():
    """Landing page for a portal user assigned to more than one facility."""
    return render_template("portal_select.html", clients=current_user.clients)


@portal_bp.route("/portal/<uuid:client_id>")
@client_user_required
def client_portal(client_id):
    client = Client.query.get_or_404(client_id)
    zones = Zone.query.filter_by(client_id=client_id).all()

    zone_data = []
    for zone in zones:
        tasks = MssTask.query.filter_by(zone_id=zone.id, active=True).all()
        task_rows = []
        for task in tasks:
            latest_completion = (
                Completion.query.join(TaskAssignment)
                .filter(TaskAssignment.mss_task_id == task.id)
                .order_by(Completion.completed_at.desc())
                .first()
            )
            task_rows.append({"task": task, "latest_completion": latest_completion})
        zone_data.append({"zone": zone, "tasks": task_rows})

    show_switcher = len(current_user.clients) > 1
    return render_template(
        "portal.html", client=client, zone_data=zone_data, show_switcher=show_switcher
    )
