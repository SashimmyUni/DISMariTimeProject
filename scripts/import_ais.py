import pandas as pd

from app import db, create_app
from app.models import ShipPosition


def import_csv(csv_path):
    app = create_app()

    with app.app_context():
        dataframe = pd.read_csv(csv_path)

        for _, row in dataframe.iterrows():
            ship = ShipPosition(
                mmsi=row["mmsi"],
                vessel_name=row.get("vessel_name"),
                latitude=row["latitude"],
                longitude=row["longitude"],
                speed=row.get("speed"),
                course=row.get("course"),
                heading=row.get("heading"),
                timestamp=pd.to_datetime(row["timestamp"]),
            )
            db.session.add(ship)

        db.session.commit()


if __name__ == "__main__":
    import_csv("data/sample_ais.csv")
