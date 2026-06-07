from datetime import date, timedelta

from flask import Blueprint, jsonify, request
import re

from app.db import normalize_timestamp, select_dicts

api = Blueprint("api", __name__)

# Input validation patterns
MMSI_RE   = re.compile(r"^\d{7,9}$")
VESSEL_RE = re.compile(r"^[A-Za-z0-9 .'\-]{1,50}$")
DATE_RE   = re.compile(r"^\d{4}-\d{2}-\d{2}$")
 

# Helpers
def parse_date_bounds(date_filter):
    """
    Parse a YYYY-MM-DD date and return (start, end) datetime bounds.
    """
    if not date_filter:
        return None, None, None

    if not DATE_RE.match(date_filter):
        return None, None, (jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400)
 
    try:
        selected_day = date.fromisoformat(date_filter)
    except ValueError:
        return None, None, (jsonify({"error": "Invalid date. Use YYYY-MM-DD."}), 400)
 
    next_day = selected_day + timedelta(days=1)
    return selected_day, next_day, None
 
# Routes
@api.route("/vessels")
def get_vessels():
    date_filter = request.args.get("date")
    start_day, end_day, date_error = parse_date_bounds(date_filter)
    if date_error:
        return date_error

    if start_day and end_day:
        rows = select_dicts(
            """
            SELECT DISTINCT ON (mmsi)
                mmsi,
                vessel_name,
                timestamp
            FROM ship_positions
            WHERE timestamp >= %s AND timestamp < %s
            ORDER BY mmsi, timestamp DESC, id DESC
            """,
            [start_day, end_day],
        )
    else:
        rows = select_dicts(
            """
            SELECT
                mmsi,
                vessel_name,
                timestamp
            FROM mv_ship_positions_latest
            ORDER BY mmsi
            """
        )

    payload = [
        {
            "mmsi": row["mmsi"],
            "vessel_name": row["vessel_name"],
            "timestamp": normalize_timestamp(row["timestamp"]),
        }
        for row in rows
    ]
    return jsonify(payload)


@api.route("/ships")
def get_ships():
    """
    Return ship positions with optional filters.
 
    Query parameters:
        mmsi        -- 7-9 digit MMSI number
        vessel      -- vessel name (partial match, max 50 chars)
        date        -- calendar day in YYYY-MM-DD format
        latest      -- if "true", return only the most recent position per vessel
    """
    where_clauses = []
    params = []
 
    # Date filter
    date_filter = request.args.get("date", "").strip()
    start_day, end_day, date_error = parse_date_bounds(date_filter or None)
    if date_error:
        return date_error
    if start_day and end_day:
        where_clauses.append("timestamp >= %s")
        where_clauses.append("timestamp < %s")
        params.extend([start_day, end_day])
 
    # MMSI filter
    mmsi_filter = request.args.get("mmsi", "").strip()
    if mmsi_filter:
        if not MMSI_RE.match(mmsi_filter):
            return jsonify({"error": "Invalid MMSI. Must be 7–9 digits."}), 400
        where_clauses.append("mmsi = %s")
        params.append(int(mmsi_filter))
 
    # Vessel name filter
    vessel_filter = request.args.get("vessel", "").strip()
    if vessel_filter:
        if not VESSEL_RE.match(vessel_filter):
            return jsonify({"error": "Invalid vessel name. Use letters, digits, spaces, . ' -"}), 400
        where_clauses.append("vessel_name ILIKE %s")
        params.append(f"%{vessel_filter}%")

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
 
    # Latest-only flag
    latest_only = request.args.get("latest", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }
 
    has_single_vessel_filter = bool(mmsi_filter or vessel_filter)
 
    if latest_only:
        if start_day and end_day:
            query = f"""
            SELECT DISTINCT ON (mmsi)
                id,
                mmsi,
                vessel_name,
                latitude,
                longitude,
                speed,
                course,
                heading,
                timestamp
            FROM ship_positions
            {where_sql}
            ORDER BY mmsi, timestamp DESC, id DESC
            """
            ships = select_dicts(query, params)
        else:
            query = f"""
            SELECT
                id,
                mmsi,
                vessel_name,
                latitude,
                longitude,
                speed,
                course,
                heading,
                timestamp
            FROM mv_ship_positions_latest
            {where_sql}
            ORDER BY mmsi
            """
            ships = select_dicts(query, params)
    else:
        limit_sql = "" if has_single_vessel_filter else "LIMIT 100"
        query = f"""
        SELECT
            id,
            mmsi,
            vessel_name,
            latitude,
            longitude,
            speed,
            course,
            heading,
            timestamp
        FROM ship_positions
        {where_sql}
        ORDER BY timestamp DESC
        {limit_sql}
        """
        ships = select_dicts(query, params)
 
    payload = []
    for ship in ships:
        payload.append(
            {
                "id": ship["id"],
                "mmsi": ship["mmsi"],
                "vessel_name": ship["vessel_name"],
                "latitude": ship["latitude"],
                "longitude": ship["longitude"],
                "speed": ship["speed"],
                "course": ship["course"],
                "heading": ship["heading"],
                "timestamp": normalize_timestamp(ship["timestamp"]),
            }
        )

    return jsonify(payload)
 