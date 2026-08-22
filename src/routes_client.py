"""Thin wrapper around the Google Routes API (computeRoutes), driving mode,
traffic-aware routing preference.

Traffic-aware vs historical: TRAFFIC_AWARE_OPTIMAL + departureTime returns a
*predictive* duration for that future departure time (Google's traffic
model), not a log of actual past drive times. staticDuration is the
no-traffic baseline for comparison.
"""

import os

import requests

COMPUTE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# Only the fields this experiment needs: both durations, distance, polyline,
# and a basic route description.
FIELD_MASK = (
    "routes.duration,"
    "routes.staticDuration,"
    "routes.distanceMeters,"
    "routes.polyline.encodedPolyline,"
    "routes.description"
)


class RoutesAPIError(Exception):
    pass


def _get_api_key():
    api_key = os.environ.get("GOOGLE_ROUTES_API_KEY")
    if not api_key:
        raise RoutesAPIError(
            "GOOGLE_ROUTES_API_KEY is not set. Add it to your .env file."
        )
    return api_key


def compute_route(
    origin_lat,
    origin_lng,
    dest_lat,
    dest_lng,
    departure_time_iso,
    traffic_model="BEST_GUESS",
):
    """Call computeRoutes for a single driving, traffic-aware route.

    departure_time_iso: RFC3339 timestamp string, must be in the future.
    traffic_model: BEST_GUESS, PESSIMISTIC, or OPTIMISTIC. Only meaningful
    with routingPreference TRAFFIC_AWARE_OPTIMAL + travelMode DRIVE (both
    fixed below), per the Routes API docs.
    Returns the first route dict from the API response.
    """
    api_key = _get_api_key()

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    body = {
        "origin": {"location": {"latLng": {"latitude": origin_lat, "longitude": origin_lng}}},
        "destination": {"location": {"latLng": {"latitude": dest_lat, "longitude": dest_lng}}},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
        "departureTime": departure_time_iso,
        "trafficModel": traffic_model,
    }

    try:
        response = requests.post(COMPUTE_ROUTES_URL, headers=headers, json=body, timeout=15)
    except requests.RequestException as e:
        raise RoutesAPIError(f"Request to Routes API failed: {e}") from e

    if response.status_code != 200:
        raise RoutesAPIError(
            f"Routes API returned {response.status_code}: {response.text}"
        )

    data = response.json()
    routes = data.get("routes")
    if not routes:
        raise RoutesAPIError(f"Routes API response had no routes: {data}")

    return routes[0]
