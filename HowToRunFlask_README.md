# How To Run Flask - Detailed Step-by-Step Guide

This guide explains exactly how to run this project from scratch.

Project folder:
DISMariTimeProject

Main run command:
python run.py

---

## 1) Prerequisites

Install the following before starting:

1. Python 3.10+ (recommended: 3.11)
2. pip (comes with Python)
3. Git (optional, if cloning from GitHub)
4. VS Code (recommended)

Check installation:

PowerShell commands:
python --version
pip --version

If python is not recognized, try:
py --version

---

## 2) Open the Project

If you already have the folder, go to it:

PowerShell commands:
cd C:\Users\Sashi\Documents\Bachelor\MartialArtsComputerVision\DISMariTimeProject

If you need to clone first:

PowerShell commands:
cd C:\Users\Sashi\Documents\Bachelor\MartialArtsComputerVision
git clone https://github.com/SashimmyUni/DISMariTimeProject.git
cd DISMariTimeProject

---

## 3) Create and Activate Virtual Environment

Create venv:

PowerShell commands:
python -m venv .venv

Activate venv (PowerShell):

PowerShell commands:
.\.venv\Scripts\Activate.ps1

If execution policy blocks activation, run this once in current terminal session:

PowerShell commands:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

Confirm virtual environment is active:

PowerShell commands:
python --version
where python

You should see python path inside .venv.

---

## 4) Install Dependencies

Install project packages:

PowerShell commands:
pip install --upgrade pip
pip install -r requirements.txt

Verify key packages:

PowerShell commands:
pip show Flask
pip show Flask-SQLAlchemy
pip show Flask-Migrate

---

## 5) Configure Environment Variables

The project includes .env.example.

Copy it to .env:

PowerShell commands:
Copy-Item .env.example .env

Open .env and set values as needed.

Default .env values:
SECRET_KEY=change-this-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dismaritime
FLASK_ENV=development

Important note:
If DATABASE_URL is not set, the app defaults to local SQLite file:
dismaritime.db

That means the easiest local run is:
- Keep .env simple, or
- Remove DATABASE_URL for SQLite mode.

---

## 6) Choose Database Mode

### Option A (Easiest): SQLite local file

Recommended for quick coursework/demo runs.

How:
1. Do not set DATABASE_URL in .env, or remove that line.
2. Start app.
3. Tables are auto-created on startup.

No separate DB server required.

### Option B: PostgreSQL

Use this if your course requires PostgreSQL.

1. Ensure PostgreSQL server is installed and running.
2. Create database named dismaritime.
3. Set DATABASE_URL in .env, for example:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dismaritime
4. Start app.
5. Tables are auto-created on startup.

---

## 7) Run the Flask App

From project root with venv active:

PowerShell commands:
python run.py

Expected output includes Flask startup messages and local URL.
Typical URL:
http://127.0.0.1:5000

Open browser and visit:
http://127.0.0.1:5000

---

## 8) Import Sample AIS Data

In a second terminal (or stop app first), from project root with venv active:

PowerShell commands:
python scripts/import_ais.py

This loads data from:
data/sample_ais.csv

Then refresh browser page.

You should see:
1. Map markers
2. Table rows in Latest Ship Positions

---

## 9) Verify API Endpoint

Check API directly in browser:
http://127.0.0.1:5000/api/ships

Or in PowerShell:

PowerShell commands:
Invoke-WebRequest http://127.0.0.1:5000/api/ships | Select-Object -ExpandProperty Content

Expected result: JSON array of ships.

---

## 10) Daily Developer Workflow

Each new session:

PowerShell commands:
cd C:\Users\Sashi\Documents\Bachelor\MartialArtsComputerVision\DISMariTimeProject
.\.venv\Scripts\Activate.ps1
python run.py

When dependencies change:

PowerShell commands:
pip install -r requirements.txt

When sample CSV changes and you want to reimport:

PowerShell commands:
python scripts/import_ais.py

---

## 11) Where to Implement New Features

1. Database tables/models:
app/models.py

2. API logic and filtering:
app/api/routes.py

3. Main page Flask routes:
app/routes.py

4. Frontend map and table behavior:
app/static/js/map.js

5. UI styling:
app/static/css/style.css

6. HTML layout:
app/templates/base.html
app/templates/index.html

---

## 12) Common Issues and Fixes

### Issue: Flask app starts but page is blank

Checks:
1. Confirm browser URL is http://127.0.0.1:5000
2. Open DevTools Console for JS errors
3. Check /api/ships endpoint returns JSON

### Issue: No markers or table rows

Checks:
1. Run data import: python scripts/import_ais.py
2. Confirm DB connection mode (SQLite vs PostgreSQL)
3. Check API output at /api/ships

### Issue: Database connection refused (PostgreSQL mode)

Fix:
1. Start PostgreSQL service
2. Verify username/password/port/database name in DATABASE_URL
3. Test with SQLite mode for quick local run

### Issue: Module not found errors

Fix:
1. Activate venv
2. Run pip install -r requirements.txt again

### Issue: PowerShell activation blocked

Fix in current session:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

---

## 13) Reset Local SQLite Database (Optional)

If using SQLite and you want a fresh start:

PowerShell commands:
Remove-Item .\dismaritime.db
python run.py
python scripts/import_ais.py

---

## 14) Recommended First Implementation Tasks

1. Add API query params (limit, mmsi filter, date range)
2. Add pagination to table
3. Add clustering for map markers
4. Add vessel detail modal on row click
5. Add CSV upload in web UI

---

## 15) Minimal Quick Start (Short Version)

PowerShell commands:
cd C:\Users\Sashi\Documents\Bachelor\MartialArtsComputerVision\DISMariTimeProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py

Then open:
http://127.0.0.1:5000

Optional data load:
python scripts/import_ais.py
