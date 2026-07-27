"""
Admin-side client management: list clients, view a single client with its
zones, create a new client, and add zones to it. This is the "onboard a
new food plant" flow.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Client, Zone

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/company/<uuid:company_id>/clients")
@staff_required
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


@clients_bp.route("/company/<uuid:company_id>/clients/new", methods=["GET", "POST"])
@staff_required
def client_new(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        client = Client(
            company_id=company_id,
            name=request.form["name"],
            address=request.form.get("address"),
            contact_name=request.form.get("contact_name"),
            contact_email=request.form.get("contact_email"),
            contact_phone=request.form.get("contact_phone"),
        )
        db.session.add(client)
        db.session.commit()
        flash(f'Client "{client.name}" created. Now add its zones below.')
        return redirect(url_for("clients.client_detail", company_id=company_id, client_id=client.id))

    return render_template(
        "client_form.html", company=company, client=None, show_sidebar=True, active_nav="clients"
    )


@clients_bp.route("/company/<uuid:company_id>/clients/<uuid:client_id>/edit", methods=["GET", "POST"])
@staff_required
def client_edit(company_id, client_id):
    company = Company.query.get_or_404(company_id)
    client = Client.query.filter_by(id=client_id, company_id=company_id).first_or_404()

    if request.method == "POST":
        client.name = request.form["name"]
        client.address = request.form.get("address")
        client.contact_name = request.form.get("contact_name")
        client.contact_email = request.form.get("contact_email")
        client.contact_phone = request.form.get("contact_phone")
        db.session.commit()
        flash(f'"{client.name}" updated.')
        return redirect(url_for("clients.client_detail", company_id=company_id, client_id=client_id))

    return render_template(
        "client_form.html", company=company, client=client, show_sidebar=True, active_nav="clients"
    )


@clients_bp.route("/company/<uuid:company_id>/clients/<uuid:client_id>")
@staff_required
def client_detail(company_id, client_id):
    company = Company.query.get_or_404(company_id)
    client = Client.query.filter_by(id=client_id, company_id=company_id).first_or_404()
    zones = Zone.query.filter_by(client_id=client_id).order_by(Zone.name).all()

    return render_template(
        "client_detail.html",
        company=company,
        client=client,
        zones=zones,
        show_sidebar=True,
        active_nav="clients",
    )


@clients_bp.route("/company/<uuid:company_id>/clients/<uuid:client_id>/zones/new", methods=["POST"])
@staff_required
def zone_new(company_id, client_id):
    # Confirm the client actually belongs to this company before attaching
    # a zone to it -- prevents a staff member from injecting a zone onto
    # another company's client by guessing a client_id.
    client = Client.query.filter_by(id=client_id, company_id=company_id).first_or_404()

    zone = Zone(
        client_id=client.id,
        name=request.form["name"],
        description=request.form.get("description"),
    )
    db.session.add(zone)
    db.session.commit()
    flash(f'Zone "{zone.name}" added to {client.name}.')
    return redirect(url_for("clients.client_detail", company_id=company_id, client_id=client_id))
