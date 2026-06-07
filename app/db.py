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

CREATE INDEX IF NOT EXISTS ix_ship_positions_timestamp_desc
    ON ship_positions (timestamp DESC);

CREATE INDEX IF NOT EXISTS ix_ship_positions_mmsi_timestamp_desc
    ON ship_positions (mmsi, timestamp DESC);

CREATE OR REPLACE VIEW v_ship_positions_latest AS
SELECT DISTINCT ON (mmsi)
    id,
    mmsi,
    vessel_name,
    latitude,
    longitude,
    speed,
    course,
    heading,
    timestamp
FROM ship_positions
ORDER BY mmsi, timestamp DESC, id DESC;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ship_positions_latest AS
SELECT DISTINCT ON (mmsi)
    id,
    mmsi,
    vessel_name,
    latitude,
    longitude,
    speed,
    course,
    heading,
    timestamp
FROM ship_positions
ORDER BY mmsi, timestamp DESC, id DESC;

CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_ship_positions_latest_mmsi
    ON mv_ship_positions_latest (mmsi);

CREATE INDEX IF NOT EXISTS ix_mv_ship_positions_latest_timestamp_desc
    ON mv_ship_positions_latest (timestamp DESC);
"""


def _database_url():
    return current_app.config["DATABASE_URL"]


def get_db_connection(database_url=None):
    return psycopg2.connect(database_url or _database_url())


def ensure_schema():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)


def refresh_latest_views():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW mv_ship_positions_latest")


def select_dicts(query, params=None):
    with get_db_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or [])
            return list(cursor.fetchall())


def normalize_timestamp(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value
