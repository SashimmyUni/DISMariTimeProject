import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    _sqlite_uri = f"sqlite:///{os.path.join(BASE_DIR, 'dismaritime.db')}"
    _postgres_default_uri = "postgresql://postgres:postgres@localhost:5432/dismaritime"
    USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"

    # Default to SQLite for low-friction local runs.
    # Set USE_POSTGRES=true to enable PostgreSQL with DATABASE_URL.
    if USE_POSTGRES:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _postgres_default_uri)
    else:
        SQLALCHEMY_DATABASE_URI = _sqlite_uri

    SQLALCHEMY_TRACK_MODIFICATIONS = False
