import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app import create_app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/dismaritime_test",
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

        self.now = datetime.now(UTC)
        self.today = self.now.date().isoformat()

    def test_index_renders_tracker_page(self):
        response = self.client.get("/")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("AIS Ship Tracker", page)

    def test_api_ships_returns_json(self):
        mocked_rows = [
            {
                "id": 1,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.29027,
                "longitude": 103.851959,
                "speed": 12.5,
                "course": 180.0,
                "heading": 175.0,
                "timestamp": self.now,
            },
            {
                "id": 2,
                "mmsi": 987654321,
                "vessel_name": "Bravo",
                "latitude": 1.3000,
                "longitude": 103.8000,
                "speed": 10.2,
                "course": 90.0,
                "heading": 95.0,
                "timestamp": self.now - timedelta(minutes=5),
            },
            {
                "id": 3,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.2900,
                "longitude": 103.8510,
                "speed": 11.0,
                "course": 178.0,
                "heading": 170.0,
                "timestamp": self.now - timedelta(minutes=30),
            },
        ]

        with patch("app.api.routes.select_dicts", return_value=mocked_rows):
            response = self.client.get("/api/ships")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload[0]["vessel_name"], "Alpha")
        self.assertIn("timestamp", payload[0])

    def test_api_ships_filters_by_date(self):
        mocked_rows = [
            {
                "id": 1,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.29027,
                "longitude": 103.851959,
                "speed": 12.5,
                "course": 180.0,
                "heading": 175.0,
                "timestamp": self.now,
            },
            {
                "id": 3,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.2900,
                "longitude": 103.8510,
                "speed": 11.0,
                "course": 178.0,
                "heading": 170.0,
                "timestamp": self.now - timedelta(minutes=30),
            },
        ]

        with patch("app.api.routes.select_dicts", return_value=mocked_rows):
            response = self.client.get(f"/api/ships?date={self.today}")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["vessel_name"], "Alpha")

    def test_api_ships_returns_latest_position_per_ship(self):
        mocked_rows = [
            {
                "id": 1,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.29027,
                "longitude": 103.851959,
                "speed": 12.5,
                "course": 180.0,
                "heading": 175.0,
                "timestamp": self.now,
            },
            {
                "id": 2,
                "mmsi": 987654321,
                "vessel_name": "Bravo",
                "latitude": 1.3000,
                "longitude": 103.8000,
                "speed": 10.2,
                "course": 90.0,
                "heading": 95.0,
                "timestamp": self.now - timedelta(minutes=5),
            },
        ]

        with patch("app.api.routes.select_dicts", return_value=mocked_rows):
            response = self.client.get("/api/ships?latest=true")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 2)

        alpha_positions = [ship for ship in payload if ship["mmsi"] == 123456789]
        self.assertEqual(len(alpha_positions), 1)

    def test_api_ships_filters_by_mmsi(self):
        mocked_rows = [
            {
                "id": 1,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.29027,
                "longitude": 103.851959,
                "speed": 12.5,
                "course": 180.0,
                "heading": 175.0,
                "timestamp": self.now,
            },
            {
                "id": 3,
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "latitude": 1.2900,
                "longitude": 103.8510,
                "speed": 11.0,
                "course": 178.0,
                "heading": 170.0,
                "timestamp": self.now - timedelta(minutes=30),
            },
        ]

        with patch("app.api.routes.select_dicts", return_value=mocked_rows):
            response = self.client.get("/api/ships?mmsi=123456789")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 2)
        self.assertTrue(all(ship["mmsi"] == 123456789 for ship in payload))

    def test_api_vessels_returns_grouped_latest_rows(self):
        mocked_rows = [
            {
                "mmsi": 123456789,
                "vessel_name": "Alpha",
                "timestamp": self.now,
            },
            {
                "mmsi": 987654321,
                "vessel_name": "Bravo",
                "timestamp": self.now - timedelta(minutes=5),
            },
        ]

        with patch("app.api.routes.select_dicts", return_value=mocked_rows):
            response = self.client.get("/api/vessels")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 2)
        mmsis = {ship["mmsi"] for ship in payload}
        self.assertSetEqual(mmsis, {123456789, 987654321})

    def test_api_ships_rejects_invalid_date(self):
        response = self.client.get("/api/ships?date=2025-99-99")

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
