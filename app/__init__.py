from flask import Flask

from config import Config
from app.db import ensure_schema


def _is_postgres_uri(uri):
    return uri.startswith("postgresql://") or uri.startswith("postgresql+psycopg2://")


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    database_uri = app.config.get("DATABASE_URL", "")
    if not app.config.get("TESTING") and not _is_postgres_uri(database_uri):
        raise RuntimeError(
            "This project only supports PostgreSQL. "
            "Set DATABASE_URL to a PostgreSQL connection string."
        )

    from app.routes import main
    from app.api.routes import api

    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix="/api")

    # Keep local setup friction low for coursework demos and quick iterations.
    if not app.config.get("TESTING"):
        with app.app_context():
            ensure_schema()

    return app
