# DISMariTimeProject

A Flask web application for displaying AIS vessel positions from a PostgreSQL database managed locally through pgAdmin.

## Database Policy

This project supports PostgreSQL only.

- The website backend reads vessel data from PostgreSQL via SQLAlchemy.
- `DATABASE_URL` must point to a PostgreSQL instance.
- SQLite is not supported for runtime use.

## Stack

- Python / Flask
- PostgreSQL
- pgAdmin (local database management)
- Flask-SQLAlchemy
- HTML, CSS, JavaScript
- Leaflet.js

## Quick Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and confirm the DB connection string:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dismaritime
```

4. Start the app:

```bash
python run.py
```

5. Open `http://127.0.0.1:5000/`.

## Data Loading

Import all cleaned AIS CSV files from `data/cleaned` into PostgreSQL:

```bash
python scripts/import_ais.py
```

Import a specific file and replace existing rows:

```bash
python scripts/import_ais.py data/cleaned/aisdk-2026-01-01-clean.csv --replace
```

The importer supports both the project sample schema (`vessel_name`, `speed`) and cleaned DMA schema (`name`, `sog`).

## API

- `GET /api/ships` returns up to 100 latest ship positions.

## Project Structure

- `app/` Flask application package
- `app/models.py` SQLAlchemy models
- `app/api/routes.py` JSON API routes
- `app/templates/` HTML templates
- `app/static/` CSS and JavaScript assets
- `scripts/` AIS data cleaning/import scripts
- `data/` sample and cleaned input files
