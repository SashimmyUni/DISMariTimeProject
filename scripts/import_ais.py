import argparse
from pathlib import Path

import pandas as pd

from app import create_app, db
from app.models import ShipPosition


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


def resolve_csv_paths(csv_source):
    source = Path(csv_source)
    if source.is_dir():
        return sorted(path for path in source.glob("*.csv") if path.is_file())
    if source.is_file():
        return [source]
    return []


def import_csv_paths(csv_paths, replace=False):
    app = create_app()

    with app.app_context():
        db.create_all()
        if replace:
            ShipPosition.query.delete()

        total_inserted = 0
        total_skipped = 0

        for csv_path in csv_paths:
            dataframe = pd.read_csv(csv_path)
            inserted = 0
            skipped = 0

            for _, row in dataframe.iterrows():
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

                ship = ShipPosition(
                    mmsi=normalized_mmsi,
                    vessel_name=pick_value(row, "vessel_name", "name", "VesselName", "Name"),
                    latitude=latitude,
                    longitude=longitude,
                    speed=parse_float(pick_value(row, "speed", "sog", "SOG")),
                    course=parse_float(pick_value(row, "course", "cog", "COG")),
                    heading=parse_float(pick_value(row, "heading", "Heading")),
                    timestamp=timestamp,
                )
                db.session.add(ship)
                inserted += 1

            db.session.commit()
            total_inserted += inserted
            total_skipped += skipped
            print(f"Imported {inserted} rows from {csv_path}.")
            if skipped:
                print(f"Skipped {skipped} invalid rows in {csv_path}.")

    print(f"Total imported rows: {total_inserted}.")
    if total_skipped:
        print(f"Total skipped rows: {total_skipped}.")


def main():
    parser = argparse.ArgumentParser(description="Import AIS CSV data into PostgreSQL.")
    parser.add_argument(
        "csv_source",
        nargs="?",
        default="data/cleaned",
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

    import_csv_paths(csv_paths, replace=args.replace)


if __name__ == "__main__":
    main()
