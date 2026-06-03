from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ship_positions (
    id SERIAL PRIMARY KEY,
    mmsi BIGINT NOT NULL,
    vessel_name VARCHAR(255),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    speed DOUBLE PRECISION,
    course DOUBLE PRECISION,
    heading DOUBLE PRECISION,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_ship_positions_mmsi
    ON ship_positions (mmsi);
"""


def _database_url():
    return current_app.config["DATABASE_URL"]


def get_db_connection(database_url=None):
    return psycopg2.connect(database_url or _database_url())


def ensure_schema():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)


def select_dicts(query, params=None):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or [])
            return list(cursor.fetchall())


def normalize_timestamp(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value
