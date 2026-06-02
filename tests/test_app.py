import unittest
from datetime import UTC, datetime, timedelta

from app import create_app, db
from app.models import ShipPosition


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            now = datetime.now(UTC)
            db.session.add(
                ShipPosition(
                    mmsi=123456789,
                    vessel_name="Alpha",
                    latitude=1.29027,
                    longitude=103.851959,
                    speed=12.5,
                    course=180.0,
                    heading=175.0,
                    timestamp=now,
                )
            )
            db.session.add(
                ShipPosition(
                    mmsi=987654321,
                    vessel_name="Bravo",
                    latitude=1.3000,
                    longitude=103.8000,
                    speed=10.2,
                    course=90.0,
                    heading=95.0,
                    timestamp=now - timedelta(minutes=5),
                )
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_renders_tracker_page(self):
        response = self.client.get("/")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("AIS Ship Tracker", page)

    def test_api_ships_returns_json(self):
        response = self.client.get("/api/ships")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["vessel_name"], "Alpha")
        self.assertIn("timestamp", payload[0])


if __name__ == "__main__":
    unittest.main()
