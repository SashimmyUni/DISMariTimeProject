"""
scripts/clean_ais.py

Cleans and compresses raw DMA AIS CSV files for use with PostgreSQL.

What it does:
  1. Strips the leading '#' from the header line (DMA quirk)
  2. Keeps only Class A vessels
  3. Requires a valid 9-digit MMSI (always present — IMO is often 'Unknown')
  4. Filters out GPS glitch coordinates (lat=91 is a known DMA placeholder)
  5. Filters to North Sea / Kattegat / Baltic corridor
  6. Downsamples to one position per vessel per 10 minutes (keyed on MMSI)
  7. Writes a lean CSV with only the columns we need

Usage:
  python scripts/clean_ais.py data/raw/aisdk-2026-01-01.csv
  python scripts/clean_ais.py data/raw/aisdk-2026-01-*.csv

Output:
  data/cleaned/aisdk-2026-01-01-clean.csv
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ── North Sea / Kattegat / Baltic corridor ────────────────────────────────
LAT_MIN, LAT_MAX = 53.5, 60.0
LON_MIN, LON_MAX =  3.0, 17.0

# ── Downsampling interval ──────────────────────────────────────────────────
SAMPLE_INTERVAL = timedelta(minutes=10)

# ── Output columns ─────────────────────────────────────────────────────────
OUTPUT_COLS = [
    "timestamp", "mmsi", "imo", "name",
    "ship_type", "cargo_type",
    "latitude", "longitude",
    "sog", "heading", "destination",
]


def parse_timestamp(raw: str) -> datetime | None:
    for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def clean_file(input_path: str) -> None:
    basename    = os.path.basename(input_path).replace(".csv", "-clean.csv")
    output_dir  = os.path.join(os.path.dirname(input_path), "..", "cleaned")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, basename)

    # last_seen[mmsi] = last timestamp written for that vessel
    last_seen: dict[str, datetime] = defaultdict(lambda: datetime.min)

    read = written = skipped = 0

    with (
        open(input_path,  newline="", encoding="utf-8") as fin,
        open(output_path, "w", newline="", encoding="utf-8") as fout,
    ):
        # DMA files start with "# Timestamp,..." — strip the leading #
        raw_header = fin.readline()
        fieldnames = [x.strip() for x in raw_header.lstrip("# ").strip().split(",")]

        reader = csv.DictReader(fin, fieldnames=fieldnames)
        writer = csv.DictWriter(fout, fieldnames=OUTPUT_COLS)
        writer.writeheader()

        for row in reader:
            read += 1

            # 1. Class A only
            if row.get("Type of mobile", "").strip() != "Class A":
                skipped += 1
                continue

            # 2. Valid MMSI (must be digits, 7-9 chars)
            mmsi = row.get("MMSI", "").strip()
            if not mmsi.isdigit() or not (7 <= len(mmsi) <= 9):
                skipped += 1
                continue

            # 3. Valid coordinates (catches GPS glitch lat=91 too)
            try:
                lat = float(row["Latitude"])
                lon = float(row["Longitude"])
            except (ValueError, KeyError):
                skipped += 1
                continue

            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                skipped += 1
                continue

            # 4. Valid timestamp
            ts = parse_timestamp(row.get("Timestamp", ""))
            if ts is None:
                skipped += 1
                continue

            # 5. Downsample — one point per vessel per 10 minutes (keyed on MMSI)
            if ts - last_seen[mmsi] < SAMPLE_INTERVAL:
                skipped += 1
                continue
            last_seen[mmsi] = ts

            # 6. IMO — keep as-is, may be 'Unknown'
            imo = row.get("IMO", "").strip()
            if not imo.isdigit() or len(imo) != 7:
                imo = None

            # 7. Write cleaned row
            writer.writerow({
                "timestamp":   ts.strftime("%Y-%m-%d %H:%M:%S"),
                "mmsi":        mmsi,
                "imo":         imo,
                "name":        row.get("Name",        "").strip() or None,
                "ship_type":   row.get("Ship type",   "").strip() or None,
                "cargo_type":  row.get("Cargo type",  "").strip() or None,
                "latitude":    lat,
                "longitude":   lon,
                "sog":         row.get("SOG",         "").strip() or None,
                "heading":     row.get("Heading",     "").strip() or None,
                "destination": row.get("Destination", "").strip() or None,
            })
            written += 1

    pct     = (written / read * 100) if read else 0
    size_mb = os.path.getsize(output_path) / 1_000_000

    print(f"  Input:   {input_path}")
    print(f"  Read:    {read:>12,} rows")
    print(f"  Written: {written:>12,} rows  ({pct:.2f}% retained)")
    print(f"  Skipped: {skipped:>12,} rows")
    print(f"  Output:  {output_path}  ({size_mb:.1f} MB)")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/clean_ais.py <file.csv> [<file2.csv> ...]")
        sys.exit(1)

    files = sys.argv[1:]
    print(f"Cleaning {len(files)} file(s)...\n")

    for path in files:
        if not os.path.isfile(path):
            print(f"  WARNING: {path} not found, skipping.")
            continue
        clean_file(path)

    print("Done.")


if __name__ == "__main__":
    main()