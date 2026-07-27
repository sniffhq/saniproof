"""
Admin-side client list: every food plant this sanitation company services,
with a quick link into each one's read-only portal (the view a client's QA
team sees) and a peek at their zones.
"""
from flask import Blueprint, render_template

from app.models import Company, Client, Zone

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/company/<uuid:company_id>/clients")
def client_list(company_id):
    company = Company.query.get_or_404(company_id)
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.name).all()

    zone_counts = {}
    for client in clients:
        zone_counts[client.id] = Zone.query.filter_by(client_id=client.id).count()

    return render_template(
        "clients_list.html",
        company=company,
        clients=clients,
        zone_counts=zone_counts,
        show_sidebar=True,
        active_nav="clients",
    )
