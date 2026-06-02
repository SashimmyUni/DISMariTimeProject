from flask import Blueprint, jsonify

from app.models import ShipPosition

api = Blueprint("api", __name__)


@api.route("/ships")
def get_ships():
    ships = ShipPosition.query.order_by(ShipPosition.timestamp.desc()).limit(100).all()
    return jsonify([ship.to_dict() for ship in ships])
