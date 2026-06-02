from app import db


class ShipPosition(db.Model):
    __tablename__ = "ship_positions"

    id = db.Column(db.Integer, primary_key=True)
    mmsi = db.Column(db.BigInteger, nullable=False, index=True)
    vessel_name = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=True)
    course = db.Column(db.Float, nullable=True)
    heading = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "mmsi": self.mmsi,
            "vessel_name": self.vessel_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed": self.speed,
            "course": self.course,
            "heading": self.heading,
            "timestamp": self.timestamp.isoformat(),
        }
