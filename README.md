# DISMariTimeProject

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
