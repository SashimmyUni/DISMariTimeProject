from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config

db = SQLAlchemy()
migrate = Migrate()


def _is_postgres_uri(uri):
    return uri.startswith("postgresql://") or uri.startswith("postgresql+psycopg2://")


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not app.config.get("TESTING") and not _is_postgres_uri(database_uri):
        raise RuntimeError(
            "This project only supports PostgreSQL. "
            "Set DATABASE_URL to a PostgreSQL connection string."
        )

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main
    from app.api.routes import api

    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix="/api")

    # Keep local setup friction low for coursework demos and quick iterations.
    with app.app_context():
        db.create_all()

    return app
