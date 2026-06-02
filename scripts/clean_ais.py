"""
scripts/clean_ais.py

Cleans and compresses raw DMA AIS CSV files for use with PostgreSQL.

What it does:
  1. Keeps only Class A vessels (large commercial ships with valid IMO)
  2. Requires a valid 7-digit IMO number
  3. Filters to North Sea / Kattegat / Baltic corridor bounding box
  4. Downsamples to one position per vessel per 10 minutes
  5. Writes a lean CSV with only the columns we need

Usage:
  python scripts/clean_ais.py data/raw/aisdk-2026-01-01.csv
  python scripts/clean_ais.py data/raw/aisdk-2026-*.csv   (multiple files)

Output:
  data/cleaned/aisdk-2026-01-01-clean.csv
  (typically ~200x smaller than the raw file)
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ── North Sea / Kattegat / Baltic corridor ────────────────────────────────
# Covers the full area DMA antennas pick up:
# south  → German Bight coast (~53.5°N)
# north  → Southern Norway (~60.0°N)
# west   → North Sea entrance (~3.0°E)
# east   → Bornholm / southern Swedish coast (~17.0°E)
LAT_MIN, LAT_MAX = 53.5, 60.0
LON_MIN, LON_MAX =  3.0, 17.0

# ── Downsampling interval ──────────────────────────────────────────────────
SAMPLE_INTERVAL = timedelta(minutes=10)

# ── Output columns ─────────────────────────────────────────────────────────
OUTPUT_COLS = [
    "timestamp", "imo", "mmsi", "name",
    "ship_type", "cargo_type",
    "latitude", "longitude",
    "sog", "heading", "destination",
]


def parse_timestamp(raw: str) -> datetime | None:
    """Try the two timestamp formats found in DMA AIS files."""
    for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def clean_file(input_path: str) -> None:
    basename   = os.path.basename(input_path).replace(".csv", "-clean.csv")
    output_dir = os.path.join(os.path.dirname(input_path), "..", "cleaned")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, basename)

    # last_seen[imo] = last timestamp written for that vessel
    last_seen: dict[str, datetime] = defaultdict(lambda: datetime.min)

    read = written = skipped = 0

    with (
        open(input_path,  newline="", encoding="utf-8") as fin,
        open(output_path, "w", newline="", encoding="utf-8") as fout,
    ):
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=OUTPUT_COLS)
        writer.writeheader()

        for row in reader:
            read += 1

            # 1. Class A only
            if row.get("Type of mobile", "").strip() != "Class A":
                skipped += 1
                continue

            # 2. Valid 7-digit IMO
            imo = row.get("IMO", "").strip()
            if not imo.isdigit() or len(imo) != 7:
                skipped += 1
                continue

            # 3. Valid coordinates within Danish waters
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

            # 5. Downsample — one point per vessel per 10 minutes
            if ts - last_seen[imo] < SAMPLE_INTERVAL:
                skipped += 1
                continue
            last_seen[imo] = ts

            # 6. Write cleaned row
            writer.writerow({
                "timestamp":   ts.strftime("%Y-%m-%d %H:%M:%S"),
                "imo":         imo,
                "mmsi":        row.get("MMSI", "").strip() or None,
                "name":        row.get("Name", "").strip() or None,
                "ship_type":   row.get("Ship type", "").strip() or None,
                "cargo_type":  row.get("Cargo type", "").strip() or None,
                "latitude":    lat,
                "longitude":   lon,
                "sog":         row.get("SOG", "").strip() or None,
                "heading":     row.get("Heading", "").strip() or None,
                "destination": row.get("Destination", "").strip() or None,
            })
            written += 1

    pct = (written / read * 100) if read else 0
    size_mb = os.path.getsize(output_path) / 1_000_000

    print(f"  Input:   {input_path}")
    print(f"  Read:    {read:>10,} rows")
    print(f"  Written: {written:>10,} rows  ({pct:.1f}% retained)")
    print(f"  Skipped: {skipped:>10,} rows")
    print(f"  Output:  {output_path}  ({size_mb:.1f} MB)")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/clean_ais.py <file.csv> [<file2.csv> ...]")
        print("Example: python scripts/clean_ais.py data/raw/aisdk-2026-01-01.csv")
        sys.exit(1)

    files = sys.argv[1:]
    print(f"Cleaning {len(files)} file(s)...\n")

    total_read = total_written = 0
    for path in files:
        if not os.path.isfile(path):
            print(f"  WARNING: {path} not found, skipping.")
            continue
        clean_file(path)

    print("Done.")


if __name__ == "__main__":
    main()