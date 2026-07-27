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

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(tasks_admin_bp)
    app.register_blueprint(sops_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(users_admin_bp)

    return app
