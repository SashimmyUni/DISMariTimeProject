# DISMariTimeProject

<<<<<<< HEAD
DISMariTimeProject is a small Flask application for importing AIS CSV files into SQLite and viewing the latest ship position and direction data in a browser.

## Features

- Upload an AIS CSV file from the web interface
- Store imported AIS rows in SQLite
- Show the latest known position and direction for each ship
- Highlight report counts and timestamps for each vessel overview row

## Expected AIS CSV columns

The importer accepts common AIS-style column names, including aliases such as:

- MMSI / Maritime Mobile Service Identity
- VesselName / Ship Name
- BaseDateTime / Timestamp / Datetime
- LAT / Latitude
- LON / Longitude / Long
- COG / Course / Course Over Ground
- Heading

At minimum, each row must provide an MMSI, latitude, and longitude column.

## Run locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the Flask app:

   ```bash
   python app.py
   ```

3. Open `http://127.0.0.1:5000/` and upload an AIS CSV file.

Each upload replaces the currently stored AIS data so the overview always reflects the latest imported file.

## Tests

Run the focused test suite with:

```bash
python -m unittest discover -s tests
```
=======
A Flask-based web application for displaying AIS shipping positions from a PostgreSQL database.

## Stack

- Python / Flask
- SQLite (default for easiest local run)
- PostgreSQL (optional, via environment variable)
- pgAdmin for database management
- HTML, CSS, JavaScript
- Leaflet.js for map display

## Project Structure

- `app/` Flask application package
- `app/templates/` HTML templates
- `app/static/` CSS and JavaScript assets
- `app/api/` JSON API routes
- `scripts/` data import scripts
- `data/` sample input data

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
	- `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` (optional for local SQLite).
4. Run the app:
	- `python run.py`

The app will auto-create tables on startup. By default it uses a local SQLite file (`dismaritime.db`) so everyone can run it quickly.

## Optional PostgreSQL Setup

If you want PostgreSQL instead of SQLite, set `DATABASE_URL` in `.env`, for example:

- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dismaritime`

Then restart the app.

## Data Import

To import the sample AIS data:

- `python scripts/import_ais.py`

After importing, refresh the site to see markers and rows.

## What Is Already Implemented

- Leaflet map on `/`
- Ships API endpoint on `/api/ships`
- Data table below the map
- Manual refresh button and periodic auto-refresh

## Easy Extension Points

- Add new columns to `ShipPosition` in `app/models.py`
- Add filters and sorting in `app/api/routes.py`
- Extend table and marker popups in `app/static/js/map.js`
- Improve layout and components in `app/static/css/style.css` and templates

## Planned Features

- Display live or imported AIS vessel positions
- Query vessel data from PostgreSQL
- Render ship markers on an interactive map
- Provide JSON API endpoints for frontend updates
>>>>>>> main
