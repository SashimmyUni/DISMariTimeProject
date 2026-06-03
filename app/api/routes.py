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
    query = ShipPosition.query
    date_filter = request.args.get("date")
    query, date_error = apply_date_filter(query, date_filter)
    if date_error:
        return date_error

    latest_only = request.args.get("latest", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    mmsi_filter = request.args.get("mmsi")
    vessel_filter = request.args.get("vessel", "").strip()

    if mmsi_filter:
        try:
            query = query.filter(ShipPosition.mmsi == int(mmsi_filter))
        except ValueError:
            return jsonify({"error": "Invalid mmsi format. Use an integer MMSI."}), 400

    if vessel_filter:
        query = query.filter(ShipPosition.vessel_name.ilike(f"%{vessel_filter}%"))

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

        ships = filtered_query.all() if has_single_vessel_filter else filtered_query.limit(100).all()
    else:
        ordered_query = query.order_by(ShipPosition.timestamp.desc())
        ships = ordered_query.all() if has_single_vessel_filter else ordered_query.limit(100).all()

    return jsonify([ship.to_dict() for ship in ships])
