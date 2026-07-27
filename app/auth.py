"""
Flask-Login wiring. Two separate tables can log in -- Staff (company
admin/crew, full access to their company's internal dashboard) and
ClientUser (a food plant's QA team, scoped to whichever clients they've
been assigned). Session cookies store a prefixed id ("staff:<uuid>" or
"client:<uuid>") so the loader knows which table to query.
"""
from functools import wraps

from flask import abort
from flask_login import LoginManager, current_user, login_required

from app.models import Staff, ClientUser

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    kind, _, raw_id = user_id.partition(":")
    if kind == "staff":
        return Staff.query.get(raw_id)
    if kind == "client":
        return ClientUser.query.get(raw_id)
    return None


def staff_required(view):
    """Require a logged-in Staff account whose company_id matches the
    company_id in the URL. Blocks staff from one company browsing into
    another company's dashboard just by editing the URL."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not isinstance(current_user, Staff):
            abort(403)
        company_id = kwargs.get("company_id")
        if company_id and str(current_user.company_id) != str(company_id):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def client_user_required(view):
    """Require a logged-in ClientUser who has been assigned the client_id
    in the URL."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not isinstance(current_user, ClientUser):
            abort(403)
        client_id = kwargs.get("client_id")
        if client_id and str(client_id) not in [str(c.id) for c in current_user.clients]:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
