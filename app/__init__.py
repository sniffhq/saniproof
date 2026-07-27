import os

from flask import Flask
from dotenv import load_dotenv

from app.extensions import db

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    from app.routes.dashboard import dashboard_bp
    from app.routes.tasks import tasks_bp
    from app.routes.portal import portal_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(portal_bp)

    return app
