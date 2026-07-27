"""
Read-only client portal: lets a food plant's QA team see cleaning
status and completion history without calling the sanitation company.

No auth wired up yet -- anyone with the client_id in the URL can view
this. Fine for a scaffold/demo, not fine once real client data is in
here. Add login + RLS before that happens.
"""
from flask import Blueprint, render_template

from app.models import Client, Zone, MssTask, TaskAssignment, Completion

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/portal/<uuid:client_id>")
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

    return render_template("portal.html", client=client, zone_data=zone_data)
