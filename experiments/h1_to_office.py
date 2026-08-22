"""Validation experiment: H1 -> OFFICE, single traffic-aware route.

Not the pipeline. Just proves the Routes API integration works end to end
for one origin before we loop over all 18.

Run from the project root: python experiments/h1_to_office.py
"""

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_loader import get_row_by_cluster_id  # noqa: E402
from routes_client import RoutesAPIError, compute_route  # noqa: E402


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    with open(PROJECT_ROOT / "config" / "config.yaml") as f:
        config = yaml.safe_load(f)

    csv_path = PROJECT_ROOT / config["origins_csv_path"]

    origin = get_row_by_cluster_id(csv_path, config["target_origin_id"])
    office = get_row_by_cluster_id(csv_path, config["office_cluster_id"])

    print(f"Origin: {origin['cluster_id']} ({origin['locality']} - {origin['representative_pocket']})")
    print(f"Destination: {office['representative_pocket']}")
    print(f"Departure time: {config['departure_time']}")
    print()

    try:
        route = compute_route(
            origin_lat=float(origin["latitude"]),
            origin_lng=float(origin["longitude"]),
            dest_lat=float(office["latitude"]),
            dest_lng=float(office["longitude"]),
            departure_time_iso=config["departure_time"],
        )
    except RoutesAPIError as e:
        print(f"Routes API call failed: {e}")
        sys.exit(1)

    print(f"Distance: {route.get('distanceMeters')} meters")
    print(f"Static duration (no traffic): {route.get('staticDuration')}")
    print(f"Traffic-aware duration: {route.get('duration')}")
    print(f"Description: {route.get('description')}")
    print(f"Encoded polyline: {route.get('polyline', {}).get('encodedPolyline')}")


if __name__ == "__main__":
    main()
