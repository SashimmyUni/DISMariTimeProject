# How To Run Flask (PostgreSQL + pgAdmin)

This guide runs the project with PostgreSQL as the only database option.

## 1) Prerequisites

- Python 3.10+
- pgAdmin 4
- PostgreSQL server (local)
- VS Code (recommended)

## 2) Create Database in pgAdmin

1. Start PostgreSQL service.
2. Open pgAdmin.
3. Create a database named `dismaritime`.
4. Ensure your PostgreSQL username/password match the connection string you will place in `.env`.

## 3) Setup Python Environment

PowerShell commands:

```powershell
cd C:\Users\Sashi\Documents\Bachelor\MartialArtsComputerVision\DISMariTimeProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Configure Environment Variables

PowerShell commands:

```powershell
Copy-Item .env.example .env
```

Then set `DATABASE_URL` in `.env` to your local PostgreSQL instance, for example:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dismaritime
SECRET_KEY=change-this-secret-key
FLASK_ENV=development
```

## 5) Run the App

PowerShell commands:

```powershell
python run.py
```

Open:

- http://127.0.0.1:5000

## 6) Load AIS Data into PostgreSQL

PowerShell commands:

```powershell
python scripts/import_ais.py
```

This command imports all `.csv` files from `data/cleaned` by default.

Optional: replace existing data while importing another file:

```powershell
python scripts/import_ais.py data/cleaned/aisdk-2026-01-01-clean.csv --replace
```

## 7) Verify API

- Browser: http://127.0.0.1:5000/api/ships

PowerShell commands:

```powershell
Invoke-WebRequest http://127.0.0.1:5000/api/ships | Select-Object -ExpandProperty Content
```

## 8) Common Issues

### PostgreSQL connection refused

- Confirm PostgreSQL service is running.
- Confirm host, port, username, password, and db name in `DATABASE_URL`.
- Test credentials inside pgAdmin.

### No markers on map

- Run `python scripts/import_ais.py`.
- Verify `/api/ships` returns JSON rows.
