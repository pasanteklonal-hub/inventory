import os
from datetime import datetime, timezone

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()
login_manager = LoginManager()


def format_local_datetime(value, date_format='%d/%m/%Y %H:%M'):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone().strftime(date_format)


def create_app():
    app = Flask(__name__)

    # Database configuration (use DATABASE_URL environment variable for Postgres)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    if database_url.startswith(('postgres://', 'postgresql://')):
        database_url = 'postgresql+psycopg2://' + database_url.split('://', 1)[1]
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.add_template_filter(format_local_datetime, 'localdatetime')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Import models so they are registered with SQLAlchemy
    from . import models  # noqa: F401

    from .controllers import register_blueprints
    register_blueprints(app)

    return app
