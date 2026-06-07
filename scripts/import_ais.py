import argparse
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from psycopg2.extras import execute_batch

from app import create_app
from app.db import get_db_connection, refresh_latest_views


PROGRESS_BAR_WIDTH = 28
PROGRESS_UPDATE_EVERY_ROWS = 25_000
DEFAULT_CLEANED_DIR = Path(__file__).resolve().parents[1] / "data" / "cleaned"


def pick_value(row, *candidates):
    for column in candidates:
        if column in row and pd.notna(row[column]):
            value = row[column]
            if isinstance(value, str):
                value = value.strip()
            if value != "":
                return value
    return None


def parse_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_timestamp(value):
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def render_progress(current, total, prefix):
    if total <= 0:
        return

    ratio = max(0.0, min(1.0, current / total))
    filled = int(ratio * PROGRESS_BAR_WIDTH)
    bar = "#" * filled + "-" * (PROGRESS_BAR_WIDTH - filled)
    percent = ratio * 100
    print(f"\r{prefix} [{bar}] {percent:6.2f}% ({current:,}/{total:,})", end="", flush=True)


def resolve_csv_paths(csv_source):
    source = Path(csv_source)
    if source.is_dir():
        return sorted(path for path in source.rglob("*.csv") if path.is_file())
    if source.is_file():
        return [source]
    return []


def import_csv_paths(csv_paths, replace=False):
    app = create_app()

    with app.app_context():
        database_url = app.config["DATABASE_URL"]

        total_inserted = 0
        total_skipped = 0

        for csv_path in csv_paths:
            dataframe = pd.read_csv(csv_path)
            inserted = 0
            skipped = 0
            total_rows = len(dataframe.index)
            rows_to_insert = []

            for index, row in dataframe.iterrows():
                current_row = index + 1
                if current_row == 1 or current_row % PROGRESS_UPDATE_EVERY_ROWS == 0:
                    render_progress(current_row, total_rows, f"Importing {Path(csv_path).name}")

                mmsi = pick_value(row, "mmsi", "MMSI")
                latitude = parse_float(pick_value(row, "latitude", "LAT", "Latitude"))
                longitude = parse_float(pick_value(row, "longitude", "LON", "Longitude", "lng"))
                timestamp = parse_timestamp(pick_value(row, "timestamp", "BaseDateTime", "Timestamp"))

                if mmsi is None or latitude is None or longitude is None or timestamp is None:
                    skipped += 1
                    continue

                try:
                    normalized_mmsi = int(str(mmsi).strip())
                except ValueError:
                    skipped += 1
                    continue

                rows_to_insert.append(
                    (
                        normalized_mmsi,
                        pick_value(row, "vessel_name", "name", "VesselName", "Name"),
                        latitude,
                        longitude,
                        parse_float(pick_value(row, "speed", "sog", "SOG")),
                        parse_float(pick_value(row, "course", "cog", "COG")),
                        parse_float(pick_value(row, "heading", "Heading")),
                        timestamp,
                    )
                )
                inserted += 1

            render_progress(total_rows, total_rows, f"Importing {Path(csv_path).name}")
            print()

            with get_db_connection(database_url) as connection:
                with connection.cursor() as cursor:
                    if replace and total_inserted == 0:
                        cursor.execute("DELETE FROM ship_positions")

                    if rows_to_insert:
                        execute_batch(
                            cursor,
                            """
                            INSERT INTO ship_positions
                                (mmsi, vessel_name, latitude, longitude, speed, course, heading, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            rows_to_insert,
                            page_size=1000,
                        )

            total_inserted += inserted
            total_skipped += skipped
            print(f"Imported {inserted} rows from {csv_path}.")
            if skipped:
                print(f"Skipped {skipped} invalid rows in {csv_path}.")

        refresh_latest_views()
        print("Refreshed materialized view: mv_ship_positions_latest.")

    print(f"Total imported rows: {total_inserted}.")
    if total_skipped:
        print(f"Total skipped rows: {total_skipped}.")


def main():
    parser = argparse.ArgumentParser(description="Import AIS CSV data into PostgreSQL.")
    parser.add_argument(
        "csv_source",
        nargs="?",
        default=str(DEFAULT_CLEANED_DIR),
        help="Path to a CSV file or a directory containing CSV files.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing ship_positions rows before importing.",
    )
    args = parser.parse_args()
    csv_paths = resolve_csv_paths(args.csv_source)
    if not csv_paths:
        raise SystemExit(
            f"No CSV files found at '{args.csv_source}'. "
            "Provide a valid CSV file path or directory."
        )

    print(f"Found {len(csv_paths)} CSV files to import from {args.csv_source}.")

    import_csv_paths(csv_paths, replace=args.replace)


if __name__ == "__main__":
    main()
