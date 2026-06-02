import csv
import io
import os
import sqlite3
from datetime import datetime

from flask import Flask, flash, redirect, render_template_string, request, url_for


CREATE_AIS_REPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS ais_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mmsi TEXT NOT NULL,
    vessel_name TEXT,
    recorded_at TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    course REAL,
    heading REAL,
    direction TEXT NOT NULL
)
"""

INDEX_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>AIS Ship Overview</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        form { margin-bottom: 1.5rem; padding: 1rem; border: 1px solid #ccc; border-radius: 0.5rem; }
        .flash { margin-bottom: 1rem; padding: 0.75rem; border-radius: 0.5rem; }
        .flash.success { background: #e8f7ec; color: #1b5e20; }
        .flash.error { background: #fdecea; color: #b71c1c; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 0.6rem; text-align: left; }
        th { background: #f4f4f4; }
        .hint { color: #555; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <h1>AIS Ship Position Overview</h1>
    <p class="hint">Upload an AIS CSV file to populate the SQL-backed ship overview below.</p>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="post" enctype="multipart/form-data">
        <label for="csv_file">AIS CSV file</label>
        <input id="csv_file" name="csv_file" type="file" accept=".csv,text/csv" required>
        <button type="submit">Import CSV</button>
    </form>

    <h2>Latest ship reports</h2>
    {% if ships %}
    <table>
        <thead>
            <tr>
                <th>MMSI</th>
                <th>Vessel</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Direction</th>
                <th>Last report time</th>
                <th>Reports imported</th>
            </tr>
        </thead>
        <tbody>
            {% for ship in ships %}
            <tr>
                <td>{{ ship["mmsi"] }}</td>
                <td>{{ ship["vessel_name"] }}</td>
                <td>{{ "%.5f"|format(ship["latitude"]) }}</td>
                <td>{{ "%.5f"|format(ship["longitude"]) }}</td>
                <td>{{ ship["direction"] }}</td>
                <td>{{ ship["recorded_at"] or "Unknown" }}</td>
                <td>{{ ship["report_count"] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No AIS data has been imported yet.</p>
    {% endif %}
</body>
</html>
"""

COLUMN_ALIASES = {
    "mmsi": ("mmsi", "maritime mobile service identity"),
    "vessel_name": ("vesselname", "vessel name", "ship name", "name"),
    "recorded_at": ("basedatetime", "timestamp", "datetime", "time", "recorded_at"),
    "latitude": ("lat", "latitude"),
    "longitude": ("lon", "long", "longitude", "lng"),
    "course": ("cog", "course", "course over ground"),
    "heading": ("heading",),
    "direction": ("direction", "cardinaldirection", "cardinal direction"),
}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or os.urandom(32),
        DATABASE=os.path.join(app.instance_path, "ais_reports.sqlite"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    init_db(app)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            uploaded_file = request.files.get("csv_file")
            if uploaded_file is None or uploaded_file.filename == "":
                flash("Please choose an AIS CSV file to upload.", "error")
                return redirect(url_for("index"))

            try:
                imported_count = import_ais_csv(app, uploaded_file.stream)
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash(f"Imported {imported_count} AIS reports into SQLite.", "success")
            return redirect(url_for("index"))

        ships = fetch_ship_overview(app)
        return render_template_string(INDEX_TEMPLATE, ships=ships)

    return app


def init_db(app):
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.execute(CREATE_AIS_REPORTS_TABLE)


def import_ais_csv(app, file_stream):
    text_stream = io.TextIOWrapper(file_stream, encoding="utf-8-sig", newline="")
    reader = csv.DictReader(text_stream)

    if reader.fieldnames is None:
        raise ValueError("The uploaded file is empty or does not contain CSV headers.")

    rows_to_insert = []
    for row_number, row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue
        rows_to_insert.append(parse_ais_row(row, row_number))

    if not rows_to_insert:
        raise ValueError("The uploaded AIS CSV file does not contain any data rows.")

    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.execute(CREATE_AIS_REPORTS_TABLE)
        connection.execute("DELETE FROM ais_reports")
        connection.executemany(
            """
            INSERT INTO ais_reports (
                mmsi, vessel_name, recorded_at, latitude, longitude, course, heading, direction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )

    return len(rows_to_insert)


def parse_ais_row(row, row_number):
    mmsi = get_required_value(row, "mmsi", row_number)
    latitude = parse_float(get_required_value(row, "latitude", row_number), "latitude", row_number)
    longitude = parse_float(get_required_value(row, "longitude", row_number), "longitude", row_number)
    course_value = get_optional_value(row, "course")
    heading_value = get_optional_value(row, "heading")
    direction_value = get_optional_value(row, "direction")
    vessel_name = get_optional_value(row, "vessel_name") or "Unknown"
    recorded_at = normalize_timestamp(get_optional_value(row, "recorded_at"))
    course = parse_float(course_value, "course", row_number, required=False)
    heading = parse_float(heading_value, "heading", row_number, required=False)
    direction = direction_value or degrees_to_compass(course if course is not None else heading)

    return (
        mmsi,
        vessel_name,
        recorded_at,
        latitude,
        longitude,
        course,
        heading,
        direction,
    )


def get_required_value(row, column_name, row_number):
    value = get_optional_value(row, column_name)
    if value is None:
        raise ValueError(f"Row {row_number} is missing the required {column_name} value.")
    return value


def get_optional_value(row, column_name):
    for candidate in COLUMN_ALIASES[column_name]:
        for key, value in row.items():
            if normalize_column_name(key) == normalize_column_name(candidate):
                cleaned = (value or "").strip()
                return cleaned or None
    return None


def normalize_column_name(column_name):
    return "".join(character.lower() for character in column_name if character.isalnum() or character == " ").strip()


def parse_float(value, field_name, row_number, required=True):
    if value is None:
        if required:
            raise ValueError(f"Row {row_number} is missing the required {field_name} value.")
        return None

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Row {row_number} has an invalid {field_name} value: {value}") from exc


def normalize_timestamp(value):
    if not value:
        return None

    for timestamp_format in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            return datetime.strptime(value, timestamp_format).isoformat(sep=" ")
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat(sep=" ")
    except ValueError:
        return value


def degrees_to_compass(degrees):
    if degrees is None:
        return "Unknown"

    direction_names = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    index = round((degrees % 360) / 45) % len(direction_names)
    return direction_names[index]


def fetch_ship_overview(app):
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT
                report.mmsi,
                report.vessel_name,
                report.recorded_at,
                report.latitude,
                report.longitude,
                report.direction,
                (
                    SELECT COUNT(*)
                    FROM ais_reports AS count_report
                    WHERE count_report.mmsi = report.mmsi
                ) AS report_count
            FROM ais_reports AS report
            WHERE report.id = (
                SELECT latest.id
                FROM ais_reports AS latest
                WHERE latest.mmsi = report.mmsi
                ORDER BY latest.recorded_at DESC, latest.id DESC
                LIMIT 1
            )
            ORDER BY report.vessel_name, report.mmsi
            """
        ).fetchall()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
