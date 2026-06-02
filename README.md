# DISMariTimeProject

A Flask-based web application for displaying AIS shipping positions from a PostgreSQL database.

## Stack

- Python / Flask
- PostgreSQL
- pgAdmin for database management
- HTML, CSS, JavaScript
- Leaflet.js for map display

## Project Structure

- `app/` Flask application package
- `app/templates/` HTML templates
- `app/static/` CSS and JavaScript assets
- `app/api/` JSON API routes
- `app/services/` AIS data logic
- `scripts/` data import scripts
- `data/` sample input data

## Setup

1. Create a virtual environment
2. Install dependencies from `requirements.txt`
3. Configure environment variables in `.env`
4. Create the PostgreSQL database
5. Run the Flask app with `python run.py`

## Planned Features

- Display live or imported AIS vessel positions
- Query vessel data from PostgreSQL
- Render ship markers on an interactive map
- Provide JSON API endpoints for frontend updates
