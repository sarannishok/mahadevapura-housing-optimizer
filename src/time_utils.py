"""Pure time-math helpers for the batch traffic-prediction experiment.

No scoring or ranking here — just arithmetic derived from a single
already-fetched traffic-aware duration: predicted arrival time and how
much buffer that leaves against the 10:20 AM arrival target.
"""

from datetime import datetime, timedelta


def parse_duration_seconds(duration_str):
    """Parse Google's duration format, e.g. "1234s", into an int of seconds."""
    return int(float(duration_str.rstrip("s")))


def compute_predicted_arrival(departure_time_iso, traffic_duration_seconds):
    """Return departure_time_iso + traffic_duration_seconds, as an ISO 8601 string."""
    departure_dt = datetime.fromisoformat(departure_time_iso)
    arrival_dt = departure_dt + timedelta(seconds=traffic_duration_seconds)
    return arrival_dt.isoformat()


def compute_arrival_buffer_minutes(predicted_arrival_iso, target_arrival_iso):
    """Positive = arrives with that much buffer before the target; negative = late."""
    predicted_dt = datetime.fromisoformat(predicted_arrival_iso)
    target_dt = datetime.fromisoformat(target_arrival_iso)
    return (target_dt - predicted_dt).total_seconds() / 60
