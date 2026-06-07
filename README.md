# DIS Maritime — AIS Ship Tracker

We built a Flask web application that lets you explore historical AIS ship positions from Danish waters on an interactive map. Ships are shown as markers on a Leaflet.js map, and you can filter by date, vessel name, or MMSI.

**Group 11:** Andreas Krone Reichl, Jimmy Huynh and Sebastian Lucas Poulsen,  
**Course:** Databases and Information Systems(NDAB21010U), Spring 2026, University of Copenhagen

---

## Database Model

The E/R diagram is in [`docs/er_diagram.png`](docs/er_diagram.png).

We use a single PostgreSQL table `ship_positions` that holds AIS position reports for Class A vessels in Danish waters. The table and indexes are created automatically when you first start the app.

SQL queries used in the app are documented in [`docs/pgadmin_queries.txt`](docs/pgadmin_queries.txt).

---

## Prerequisites

- Python 3.10+
- PostgreSQL 13+ (running locally)
- pgAdmin 4 (for creating the database)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/SashimmyUni/DISMariTimeProject.git
cd DISMariTimeProject
```

### 2. Create a virtual environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the database

In pgAdmin, create a database called `dismaritime`. Or with psql:

```bash
psql -U postgres -c "CREATE DATABASE dismaritime;"
```

### 5. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your PostgreSQL password:

```env
DATABASE_URL=postgresql://postgres:YOURPASSWORD@localhost:5432/dismaritime
SECRET_KEY=change-this-secret-key
FLASK_ENV=development
```

---

## Loading Data

We use cleaned AIS data from the Danish Maritime Authority. The cleaned CSV files are in `data/cleaned/`.

**Quick demo — one day:**
```bash
python scripts/import_ais.py data/cleaned/aisdk-2026-01-01-clean.csv
```

**One week:**
```bash
python scripts/import_ais.py data/cleaned/aisdk-2026-01-01-clean.csv
python scripts/import_ais.py data/cleaned/aisdk-2026-01-02-clean.csv
python scripts/import_ais.py data/cleaned/aisdk-2026-01-03-clean.csv
python scripts/import_ais.py data/cleaned/aisdk-2026-01-04-clean.csv
python scripts/import_ais.py data/cleaned/aisdk-2026-01-05-clean.csv
python scripts/import_ais.py data/cleaned/aisdk-2026-01-06-clean.csv
python scripts/import_ais.py data/cleaned/aisdk-2026-01-07-clean.csv
```

**All of January:**
```bash
python scripts/import_ais.py
```

To clear existing data before importing, add `--replace`:
```bash
python scripts/import_ais.py --replace
```

---

## Running the App

```bash
python run.py
```

Go to **http://127.0.0.1:5000** in your browser.

---

## How to Use the App

### Map

The map shows ship positions in Danish waters — North Sea, Kattegat, and the Baltic corridor. Each dot is a ship position, and the small line through it shows the ship's heading.

### Filters

| Filter | What it does |
|--------|-------------|
| **Date** | Show positions for a specific day |
| **Vessel** | Pick a specific ship from the dropdown |
| **Latest position only** | Show only the most recent position per vessel |

All inputs are validated with regular expressions before hitting the database:
- **MMSI** must be 7–9 digits
- **Vessel name** allows letters, digits, spaces, `.`, `'`, `-`
- **Date** must be `YYYY-MM-DD`

### Ship route

Select a vessel (without "Latest position only") and the app draws its full route for the selected day as a dashed line. Green = start, red = end.

### API

You can also query the API directly:

```
GET /api/ships                      — latest 100 positions
GET /api/ships?date=2026-01-01      — positions for a specific day
GET /api/ships?mmsi=219001431       — all positions for one vessel
GET /api/ships?latest=true          — latest position per vessel
GET /api/vessels                    — list of all vessels
```

---

## Data

We download weekly AIS CSV files from [web.ais.dk/aisdata](http://web.ais.dk/aisdata/) and clean them with `scripts/clean_ais.py`:
- Only Class A vessels
- Bounding box: lat 53.5–60.0, lon 3.0–17.0
- Downsampled to one position per vessel per 10 minutes

---

## Project Structure

```
DISMariTimeProject/
├── app/
│   ├── __init__.py        — Flask app factory
│   ├── db.py              — PostgreSQL connection and schema
│   ├── routes.py          — Main page route
│   └── api/
│       └── routes.py      — JSON API with regex validation
├── app/static/
│   ├── css/style.css
│   └── js/map.js          — Leaflet map and ship route
├── app/templates/
│   ├── base.html
│   └── index.html
├── data/
│   ├── cleaned/           — Cleaned AIS CSV files
│   └── raw/               — Raw files (git-ignored)
├── docs/
│   ├── er_diagram.png     — E/R diagram
│   └── pgadmin_queries.txt — SQL queries used in the app
├── scripts/
│   ├── clean_ais.py       — Data cleaning pipeline
│   └── import_ais.py      — PostgreSQL loader
├── .env.example
├── AI_DECLARATION.md
├── config.py
├── requirements.txt
└── run.py
```

---

## Common Issues

**PostgreSQL connection refused** — check that PostgreSQL is running and that the credentials in `.env` are correct.

**No ships on map** — run `import_ais.py` first and check that `/api/ships` returns data.

**`venv\Scripts\activate` not found** — run `python -m venv venv` first, or use PowerShell with the right execution policy.