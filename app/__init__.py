import os

from flask import Flask
from dotenv import load_dotenv

from app.extensions import db
from app.auth import login_manager

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SOP_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SDS_UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.tasks import tasks_bp
    from app.routes.tasks_admin import tasks_admin_bp
    from app.routes.sops import sops_bp
    from app.routes.portal import portal_bp
    from app.routes.clients import clients_bp
    from app.routes.users_admin import users_admin_bp
    from app.routes.schedule import schedule_bp
    from app.routes.issues import issues_bp
    from app.routes.certifications import certifications_bp
    from app.routes.chemicals import chemicals_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(tasks_admin_bp)
    app.register_blueprint(sops_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(users_admin_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(certifications_bp)
    app.register_blueprint(chemicals_bp)
    app.register_blueprint(reports_bp)

    @app.context_processor
    def inject_nav_sections():
        # (breadcrumb label, list-view endpoint) for each sidebar section --
        # used by base_admin.html to build the "Dashboard / Section / ..."
        # breadcrumb trail without every route having to pass it explicitly.
        return {
            "nav_sections": {
                "schedule": ("Schedule", "schedule.schedule_list"),
                "tasks": ("Tasks", "tasks_admin.task_list"),
                "issues": ("Issues", "issues.issue_list"),
                "chemicals": ("Chemicals", "chemicals.chemical_list"),
                "sops": ("SOPs", "sops.sop_list"),
                "clients": ("Clients", "clients.client_list"),
                "users": ("Users", "users_admin.user_list"),
                "certifications": ("Certifications", "certifications.cert_list"),
                "reports": ("Reports", "reports.report_list"),
            }
        }

    return app
