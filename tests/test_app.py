import io
import os
import tempfile
import unittest

from app import create_app


class AisAppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "test.sqlite")
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": self.database_path,
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_imports_csv_and_shows_latest_ship_positions(self):
        csv_payload = """MMSI,VesselName,BaseDateTime,LAT,LON,COG,Heading
123456789,Alpha,2024-01-01T10:00:00,1.2345,103.9876,90,88
123456789,Alpha,2024-01-01T11:00:00,1.3345,104.0876,135,140
987654321,Bravo,2024-01-01T09:00:00,2.2222,105.1111,,270
"""

        response = self.client.post(
            "/",
            data={"csv_file": (io.BytesIO(csv_payload.encode("utf-8")), "ais.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Imported 3 AIS reports into SQLite.", page)
        self.assertIn("Alpha", page)
        self.assertIn("1.33450", page)
        self.assertIn("104.08760", page)
        self.assertIn("SE", page)
        self.assertIn("Bravo", page)
        self.assertIn("W", page)
        self.assertIn(">2<", page)

    def test_upload_rejects_missing_required_columns(self):
        csv_payload = """VesselName,BaseDateTime,LAT,LON
Alpha,2024-01-01T10:00:00,1.2345,103.9876
"""

        response = self.client.post(
            "/",
            data={"csv_file": (io.BytesIO(csv_payload.encode("utf-8")), "ais.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("missing the required mmsi value", page.lower())

    def test_upload_accepts_common_underscore_column_aliases(self):
        csv_payload = """mmsi,vessel_name,recorded_at,latitude,longitude,heading
111222333,Underscore,2024-01-02 08:00:00,1.1000,103.7000,180
"""

        response = self.client.post(
            "/",
            data={"csv_file": (io.BytesIO(csv_payload.encode("utf-8")), "ais.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Underscore", page)
        self.assertIn("S", page)


if __name__ == "__main__":
    unittest.main()
