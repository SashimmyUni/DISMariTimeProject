from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func
import re

from app.models import ShipPosition

api = Blueprint("api", __name__)

# Input validation patterns
MMSI_RE   = re.compile(r"^\d{7,9}$")
VESSEL_RE = re.compile(r"^[A-Za-z0-9 .'\-]{1,50}$")
DATE_RE   = re.compile(r"^\d{4}-\d{2}-\d{2}$")
 

# Helpers
def apply_date_filter(query, date_filter):
    """
    Filter query to a single calendar day. Returns (query, erorr) tuple.
    """
    if not date_filter:
        return query, None

    if not DATE_RE.match(date_filter):
        return None, (jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400)
 
    try:
        selected_day = date.fromisoformat(date_filter)
    except ValueError:
        return None, (jsonify({"error": "Invalid date. Use YYYY-MM-DD."}), 400)
 
    next_day = selected_day + timedelta(days=1)
    return (
        query.filter(
            ShipPosition.timestamp >= selected_day,
            ShipPosition.timestamp < next_day,
        ),
        None,
    )
 
def apply_limit(query, limit_param):
    """
    Apply a limit to the query. Returns (results, error) tuple
    """ 
    if limit_param == "all":
        return query.all(), None
    
    try: 
        limit = int(limit_param)
        if limit_val <= 0:
            raise ValueError()
        return query.limit(limit_val).all(), None
    except ValueError:
        return None, (jsonify({"error": "Invalid limit. Use a positive integer or 'all'."}), 400)

# Routes
@api.route("/vessels")
def get_vessels():
    query = ShipPosition.query
    date_filter = request.args.get("date")
    query, date_error = apply_date_filter(query, date_filter)
    if date_error:
        return date_error

    latest_subquery = (
        query.with_entities(
            ShipPosition.mmsi.label("mmsi"),
            func.max(ShipPosition.timestamp).label("latest_timestamp"),
        )
        .group_by(ShipPosition.mmsi)
        .subquery()
    )

    rows = (
        query.join(
            latest_subquery,
            (ShipPosition.mmsi == latest_subquery.c.mmsi)
            & (ShipPosition.timestamp == latest_subquery.c.latest_timestamp),
        )
        .with_entities(
            ShipPosition.mmsi,
            ShipPosition.vessel_name,
            ShipPosition.timestamp,
        )
        .order_by(ShipPosition.timestamp.desc())
        .all()
    )

    payload = [
        {
            "mmsi": row.mmsi,
            "vessel_name": row.vessel_name,
            "timestamp": row.timestamp.isoformat(),
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
    query = ShipPosition.query
 
    # Date filter
    date_filter = request.args.get("date", "").strip()
    query, date_error = apply_date_filter(query, date_filter or None)
    if date_error:
        return date_error
 
    # MMSI filter
    mmsi_filter = request.args.get("mmsi", "").strip()
    if mmsi_filter:
        if not MMSI_RE.match(mmsi_filter):
            return jsonify({"error": "Invalid MMSI. Must be 7–9 digits."}), 400
        query = query.filter(ShipPosition.mmsi == int(mmsi_filter))
 
    # Vessel name filter
    vessel_filter = request.args.get("vessel", "").strip()
    if vessel_filter:
        if not VESSEL_RE.match(vessel_filter):
            return jsonify({"error": "Invalid vessel name. Use letters, digits, spaces, . ' -"}), 400
        query = query.filter(ShipPosition.vessel_name.ilike(f"%{vessel_filter}%"))
 
    # Latest-only flag
    latest_only = request.args.get("latest", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }

    # Limit parameter
    limit_param = request.args.get("limit", "100").strip()
 
    has_single_vessel_filter = bool(mmsi_filter or vessel_filter)
 
    if latest_only:
        latest_subquery = (
            query.with_entities(
                ShipPosition.mmsi.label("mmsi"),
                func.max(ShipPosition.timestamp).label("latest_timestamp"),
            )
            .group_by(ShipPosition.mmsi)
            .subquery()
        )
 
        filtered_query = query.join(
            latest_subquery,
            (ShipPosition.mmsi == latest_subquery.c.mmsi)
            & (ShipPosition.timestamp == latest_subquery.c.latest_timestamp),
        ).order_by(ShipPosition.timestamp.desc())
 
        ships = (
            filtered_query.all()
            if (has_single_vessel_filter or latest_only)
            else filtered_query.limit(100).all()
        )
    else:
        ordered_query = query.order_by(ShipPosition.timestamp.desc())
        if has_single_vessel_filter:
            ships = ordered_query.all()
        else:
            ships, limit_error = apply_limit(ordered_query, limit_param)
            if limit_error:
                return limit_error
 
    return jsonify([ship.to_dict() for ship in ships])
 