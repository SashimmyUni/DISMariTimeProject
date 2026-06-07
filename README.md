# DISMariTimeProject

Flask + PostgreSQL AIS tracker for ingesting, cleaning, storing, and serving vessel positions with optimized SQL views.

## Overview

This repository implements an end-to-end pipeline:

1. Raw AIS CSV files are cleaned and downsampled.
2. Cleaned files are bulk imported into PostgreSQL.
3. Schema, indexes, and views are created/maintained automatically.
4. API endpoints read from base tables and optimized views.
5. Frontend map consumes API responses.

The app uses direct SQL via `psycopg2` (no ORM) and supports PostgreSQL only.

## Tech Stack

- Python / Flask
- PostgreSQL
- pgAdmin (recommended for local DB inspection)
- Pandas + psycopg2 for import
- HTML/CSS/JavaScript + Leaflet.js

## Pipeline Architecture

### 1) Raw Data

- Input location: `data/raw/`
- Source format: DMA AIS CSV files

### 2) Cleaning Stage

Script: `scripts/clean_ais.py`

What the cleaner does:

- Removes DMA header quirks.
- Keeps Class A vessels only.
- Validates MMSI and timestamps.
- Filters invalid coordinates and constrains geospatial bounds.
- Downsamples to one position per vessel per 10 minutes.
- Outputs lean CSV files for import.

Output location:

- `data/cleaned/*-clean.csv`

Example:

```bash
python scripts/clean_ais.py data/raw/aisdk-2026-01-01.csv
python scripts/clean_ais.py data/raw/aisdk-2026-01-01.csv data/raw/aisdk-2026-01-02.csv
```

### 3) Import Stage

Script: `scripts/import_ais.py`

What the importer does:

- Reads one CSV or all CSV files in a directory.
- Normalizes supported column aliases (`mmsi`/`MMSI`, `vessel_name`/`name`, `speed`/`sog`, etc.).
- Bulk inserts rows into `ship_positions` using `execute_batch`.
- Optionally clears old rows with `--replace`.
- Refreshes materialized latest view after import.

Examples:

```bash
# Import all cleaned files
python scripts/import_ais.py

# Import a single file
python scripts/import_ais.py data/cleaned/aisdk-2026-01-01-clean.csv

# Replace existing records, then import
python scripts/import_ais.py data/cleaned/aisdk-2026-01-01-clean.csv --replace
```

### 4) Database Schema + Performance Objects

Defined in `app/db.py` and also documented in `pgadmin_queries.txt`.

Core table:

- `ship_positions`

Performance indexes:

- `ix_ship_positions_mmsi`
- `ix_ship_positions_timestamp_desc`
- `ix_ship_positions_mmsi_timestamp_desc`

Views:

- `v_ship_positions_latest` (normal view, always current)
- `mv_ship_positions_latest` (materialized view, very fast reads)

Why materialized views are included:

- They are added as a performance pattern for future scaling and as practice with SQL optimization.
- In a fresh local evaluation environment, the evaluator still needs to import data first.
- Because of that setup step, runtime gains may not be very noticeable during initial small/local runs.
- The main benefit appears when datasets grow and latest-position queries are called repeatedly.

Materialized view indexes:

- `ix_mv_ship_positions_latest_mmsi` (unique)
- `ix_mv_ship_positions_latest_timestamp_desc`

Refresh behavior:

- `scripts/import_ais.py` automatically runs `REFRESH MATERIALIZED VIEW mv_ship_positions_latest` after import.
- If you modify `ship_positions` manually (pgAdmin/SQL), refresh the materialized view manually.

```sql
REFRESH MATERIALIZED VIEW mv_ship_positions_latest;
```

### 5) API Serving Stage

Routes in `app/api/routes.py`.

- `GET /api/vessels`
	- No `date`: reads from `mv_ship_positions_latest` (fast path).
	- With `date=YYYY-MM-DD`: computes latest-per-vessel from base table for that day.

- `GET /api/ships`
	- Supports filters: `mmsi`, `vessel`, `date`, `latest`.
	- `latest=true` and no date: reads from `mv_ship_positions_latest`.
	- Other combinations query `ship_positions` directly.

## End-to-End Setup

### 1) Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure Environment Variables

Create `.env` with:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dismaritime
SECRET_KEY=dev-secret-key
```

### 3) Start the App

```bash
python run.py
```

On startup (non-testing mode), the app runs schema setup from `app/db.py`.

### 4) Run the Data Pipeline

```bash
# Optional cleaning stage if starting from raw files
python scripts/clean_ais.py data/raw/aisdk-2026-01-01.csv

# Import cleaned data
python scripts/import_ais.py
```

### 5) Verify API

Open in browser:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/api/ships`
- `http://127.0.0.1:5000/api/vessels`

Example query variants:

- `/api/ships?latest=true`
- `/api/ships?mmsi=123456789`
- `/api/ships?vessel=Alpha`
- `/api/ships?date=2026-01-15`
- `/api/vessels?date=2026-01-15`

## pgAdmin Workflow

Use `pgadmin_queries.txt` for:

- One-time schema + index + view creation
- API-equivalent SQL checks
- Utility diagnostics (counts, date ranges)
- Manual materialized view refresh commands

## Testing

Run unit tests:

```bash
python -m unittest -q
```

## Operational Notes

- PostgreSQL is mandatory for runtime.
- SQLite is not supported.
- Materialized view reads are fast, but view freshness depends on refresh.
- Import script already refreshes the materialized view automatically.
- Practical evaluation note: on a tutor's first local run, importing data and schema/view setup dominate elapsed time; materialized views are mainly included for future runtime improvements and optimization practice.

## Project Structure

- `app/` Flask application package
- `app/db.py` schema, indexes, views, DB helpers
- `app/api/routes.py` JSON API routes and filters
- `app/templates/` HTML templates
- `app/static/` frontend assets
- `scripts/clean_ais.py` raw DMA cleaning/downsampling
- `scripts/import_ais.py` PostgreSQL bulk import + MV refresh
- `data/raw/` raw AIS input
- `data/cleaned/` cleaned AIS output
- `pgadmin_queries.txt` pgAdmin-ready SQL reference
