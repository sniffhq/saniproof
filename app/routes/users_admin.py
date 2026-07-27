"""
Account management: create staff logins (full access to this company's
internal dashboard) and client-portal logins (scoped to one or more
assigned clients). This is the only place new accounts get created --
there's no self-signup.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Staff, Client, ClientUser

users_admin_bp = Blueprint("users_admin", __name__)


@users_admin_bp.route("/company/<uuid:company_id>/users")
@staff_required
def user_list(company_id):
    company = Company.query.get_or_404(company_id)
    staff = Staff.query.filter_by(company_id=company_id).order_by(Staff.name).all()

    client_ids = [c.id for c in Client.query.filter_by(company_id=company_id).all()]
    portal_users = (
        ClientUser.query.filter(ClientUser.clients.any(Client.company_id == company_id))
        .order_by(ClientUser.name)
        .all()
        if client_ids
        else []
    )

    return render_template(
        "users_list.html",
        company=company,
        staff=staff,
        portal_users=portal_users,
        show_sidebar=True,
        active_nav="users",
    )


@users_admin_bp.route("/company/<uuid:company_id>/users/staff/new", methods=["GET", "POST"])
@staff_required
def staff_new(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        existing = Staff.query.filter(Staff.email == request.form["email"].strip().lower()).first()
        if existing:
            flash("A staff account with that email already exists.", "error")
            return render_template(
                "staff_user_form.html", company=company, show_sidebar=True, active_nav="users"
            )

        member = Staff(
            company_id=company_id,
            name=request.form["name"],
            email=request.form["email"].strip().lower(),
            role=request.form["role"],
            phone=request.form.get("phone") or None,
        )
        member.set_password(request.form["password"])
        db.session.add(member)
        db.session.commit()
        flash(f'Staff account created for {member.name}.')
        return redirect(url_for("users_admin.user_list", company_id=company_id))

    return render_template(
        "staff_user_form.html", company=company, member=None, show_sidebar=True, active_nav="users"
    )


@users_admin_bp.route("/company/<uuid:company_id>/users/staff/<uuid:staff_id>/edit", methods=["GET", "POST"])
@staff_required
def staff_edit(company_id, staff_id):
    company = Company.query.get_or_404(company_id)
    member = Staff.query.filter_by(id=staff_id, company_id=company_id).first_or_404()

    if request.method == "POST":
        member.name = request.form["name"]
        member.role = request.form["role"]
        member.phone = request.form.get("phone") or None
        new_password = request.form.get("password")
        if new_password:
            member.set_password(new_password)
        db.session.commit()
        flash(f'"{member.name}" updated.')
        return redirect(url_for("users_admin.user_list", company_id=company_id))

    return render_template(
        "staff_user_form.html", company=company, member=member, show_sidebar=True, active_nav="users"
    )


@users_admin_bp.route("/company/<uuid:company_id>/users/staff/<uuid:staff_id>/toggle-active", methods=["POST"])
@staff_required
def staff_toggle_active(company_id, staff_id):
    member = Staff.query.filter_by(id=staff_id, company_id=company_id).first_or_404()
    member.active = not member.active
    db.session.commit()
    flash(f'{member.name} is now {"active" if member.active else "deactivated"}.')
    return redirect(url_for("users_admin.user_list", company_id=company_id))


@users_admin_bp.route("/company/<uuid:company_id>/users/clients/new", methods=["GET", "POST"])
@staff_required
def client_user_new(company_id):
    company = Company.query.get_or_404(company_id)
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.name).all()

    if request.method == "POST":
        existing = ClientUser.query.filter(
            ClientUser.email == request.form["email"].strip().lower()
        ).first()
        if existing:
            flash("A client portal account with that email already exists.", "error")
            return render_template(
                "client_user_form.html",
                company=company,
                clients=clients,
                show_sidebar=True,
                active_nav="users",
            )

        selected_ids = request.form.getlist("client_ids")
        member = ClientUser(
            name=request.form["name"],
            email=request.form["email"].strip().lower(),
            role=request.form.get("role", "viewer"),
        )
        member.set_password(request.form["password"])
        member.clients = [c for c in clients if str(c.id) in selected_ids]
        db.session.add(member)
        db.session.commit()
        flash(f'Client portal account created for {member.name}.')
        return redirect(url_for("users_admin.user_list", company_id=company_id))

    return render_template(
        "client_user_form.html",
        company=company,
        clients=clients,
        member=None,
        show_sidebar=True,
        active_nav="users",
    )


@users_admin_bp.route("/company/<uuid:company_id>/users/clients/<uuid:user_id>/edit", methods=["GET", "POST"])
@staff_required
def client_user_edit(company_id, user_id):
    company = Company.query.get_or_404(company_id)
    clients = Client.query.filter_by(company_id=company_id).order_by(Client.name).all()
    member = ClientUser.query.filter(
        ClientUser.id == user_id, ClientUser.clients.any(Client.company_id == company_id)
    ).first()
    if not member:
        # Also allow editing a portal user who currently has zero clients
        # assigned (e.g. all were removed) but was created for this company.
        member = ClientUser.query.get_or_404(user_id)

    if request.method == "POST":
        member.name = request.form["name"]
        member.role = request.form.get("role", "viewer")
        selected_ids = request.form.getlist("client_ids")
        member.clients = [c for c in clients if str(c.id) in selected_ids]
        new_password = request.form.get("password")
        if new_password:
            member.set_password(new_password)
        db.session.commit()
        flash(f'"{member.name}" updated.')
        return redirect(url_for("users_admin.user_list", company_id=company_id))

    return render_template(
        "client_user_form.html",
        company=company,
        clients=clients,
        member=member,
        show_sidebar=True,
        active_nav="users",
    )


@users_admin_bp.route("/company/<uuid:company_id>/users/clients/<uuid:user_id>/toggle-active", methods=["POST"])
@staff_required
def client_user_toggle_active(company_id, user_id):
    member = ClientUser.query.get_or_404(user_id)
    member.active = not member.active
    db.session.commit()
    flash(f'{member.name} is now {"active" if member.active else "deactivated"}.')
    return redirect(url_for("users_admin.user_list", company_id=company_id))
