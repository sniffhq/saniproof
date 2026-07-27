from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func

from app.models import Staff, ClientUser

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = Staff.query.filter(func.lower(Staff.email) == email).first()
        if not user:
            user = ClientUser.query.filter(func.lower(ClientUser.email) == email).first()

        if user and user.check_password(password):
            if not user.active:
                flash("This account has been deactivated. Contact your admin.", "error")
            elif login_user(user):
                return _redirect_after_login(user)
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


def _redirect_after_login(user):
    if isinstance(user, Staff):
        return redirect(url_for("dashboard.company_dashboard", company_id=user.company_id))

    # ClientUser: go straight to their portal if they only have one client,
    # otherwise show a picker.
    if len(user.clients) == 1:
        return redirect(url_for("portal.client_portal", client_id=user.clients[0].id))
    return redirect(url_for("portal.client_select"))
