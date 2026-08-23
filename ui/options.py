"""V1 dropdown option registry for the "Find Areas" prototype.

V1 ships exactly one office, one distance, and one travel mode. The shapes
below exist so that adding a future office/distance/mode is a registry
addition -- not a rewrite of ui/data_access.py or app.py. In particular,
each office owns its OWN dataset file paths: a second office would point
at its own commute-score/origins/route-distance CSVs, not share
Mahadevapura's.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# office display name -> where its read-only V1 datasets live, and which
# cluster_id in its origins CSV represents the office itself.
V1_OFFICES = {
    "Mahadevapura": {
        "origins_csv": PROJECT_ROOT / "data" / "residential_origins_FROZEN_v1.csv",
        "batch_results_csv": PROJECT_ROOT / "data" / "interim" / "batch_traffic_results.csv",
        "commute_score_csv": PROJECT_ROOT / "data" / "interim" / "commute_score_v1.csv",
        "origin_summary_csv": PROJECT_ROOT / "data" / "interim" / "origin_departure_time_summary.csv",
        "office_cluster_id": "OFFICE",
    },
}

# Distance options, in km. A future distance value is just another entry
# here -- filtering logic in ui/data_access.py already takes an arbitrary
# max_distance_km.
V1_DISTANCES_KM = [5]

# Travel mode options. V1's route data (batch_traffic_results.csv) was
# fetched with Car as the driving mode, so "Car" is the only mode with
# real data behind it right now. A future mode requires its own route
# data, associated via V1_OFFICES the same way a future office would be.
V1_TRAVEL_MODES = ["Car"]
