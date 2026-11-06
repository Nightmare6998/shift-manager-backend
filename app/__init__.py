import os
from pathlib import Path
import sqlite3
from dotenv import load_dotenv
from flask import Blueprint, Flask, jsonify
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.config import config_by_name, environment_config
from app.errors import register_error_handlers
from app.extensions import db, migrate


@event.listens_for(Engine, "connect")
def enable_foreign_keys(connection, record):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")


def create_app(config_name=None):
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    name = config_name or os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development"))
    if name not in config_by_name:
        raise ValueError(f"Unknown config: {name}")
    app = Flask(__name__)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_object(config_by_name[name])
    app.config.update(environment_config(name))
    db.init_app(app)
    migrate.init_app(app, db)

    from app import models
    from app.auth.routes import auth_bp
    from app.users.routes import users_bp
    from app.shifts.routes import shifts_bp
    from app.admin.routes import admin_bp
    from app.cli import create_admin

    health_bp = Blueprint("health", __name__)

    @health_bp.get("/health")
    def health():
        return jsonify(status="ok")

    for blueprint in (health_bp, auth_bp, users_bp, shifts_bp, admin_bp):
        app.register_blueprint(blueprint)
    app.cli.add_command(create_admin)
    register_error_handlers(app)
    return app
