"""Read-only data access for the "Find Areas" prototype.

Reads only from the existing, already-computed V1 datasets registered in
ui/options.py:
  - data/residential_origins_FROZEN_v1.csv        (frozen, read-only)
  - data/interim/batch_traffic_results.csv         (existing route data --
    distance_meters here is the actual road distance already computed by
    the Routes API pipeline; this module makes no API calls of its own)
  - data/interim/commute_score_v1.csv              (existing scoring output,
    locality-level -- the locality commute score is never recomputed here)
  - data/interim/origin_departure_time_summary.csv (existing per-anchor
    descriptive summary, already computed by
    analysis/summarize_commute_reliability.py -- read-only)

No scoring, filtering-threshold, or commute-analysis logic is reimplemented
here. This module only loads, joins on locality/cluster_id, and annotates
each locality -- and each of its representative anchors -- with whether it
falls within the user's preferred distance. All analyzed localities, and
EVERY one of their representative anchors, are always returned -- distance
preference is a status label, not a filter.
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from data_loader import load_rows  # noqa: E402 -- reuses the existing frozen-origins reader

from ui.options import V1_OFFICES


def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _anchor_distances_km(batch_results_csv, office_cluster_id):
    """origin_cluster_id -> road distance to the office, in km.

    Sourced directly from distance_meters in the existing route data
    (actual driving distance, not straight-line). A given origin's
    distance is effectively constant across departure times, so the
    first value seen for each origin is kept.
    """
    distances = {}
    for row in _load_csv(batch_results_csv):
        if row["destination_cluster_id"] != office_cluster_id:
            continue
        if row["status"] != "success":
            continue
        origin = row["origin_cluster_id"]
        distances.setdefault(origin, float(row["distance_meters"]) / 1000)
    return distances


def _anchor_travel_minutes(origin_summary_csv):
    """(origin_cluster_id, departure_time) -> per-anchor typical/slower-
    traffic travel time in minutes, sourced directly from the existing
    origin_departure_time_summary.csv (already computed, read-only). This
    is the anchor-level counterpart of the locality-level median/p90
    columns in commute_score_v1.csv -- no new duration computation."""
    lookup = {}
    for row in _load_csv(origin_summary_csv):
        key = (row["origin_cluster_id"], row["departure_time"])
        lookup[key] = {
            "median_travel_minutes": float(row["median_traffic_duration_seconds"]) / 60,
            "p90_travel_minutes": float(row["p90_traffic_duration_seconds"]) / 60,
        }
    return lookup


def _best_commute_row_per_locality(commute_score_csv):
    """locality -> the commute_score_v1.csv row with the highest
    commute_score for that locality (i.e. that locality's best
    departure-time slot). latest_fully_reliable_departure is identical
    across a locality's rows already, so picking any one row is safe."""
    best = {}
    for row in _load_csv(commute_score_csv):
        locality = row["locality"]
        score = float(row["commute_score"])
        if locality not in best or score > float(best[locality]["commute_score"]):
            best[locality] = row
    return best


def get_localities(office_key):
    """All localities for `office_key`, each carrying its FULL set of
    representative anchors (every one -- never collapsed to a single
    closest anchor), plus that locality's unchanged best-slot commute
    metrics. Each anchor carries its own road distance and its own
    typical/slower-traffic travel time (looked up at the locality's
    best departure-time slot, so anchor times and the locality score stay
    consistent with each other). No distance filtering is applied here --
    see annotate_range_status."""
    config = V1_OFFICES[office_key]

    origins = load_rows(config["origins_csv"])
    anchor_distances_km = _anchor_distances_km(
        config["batch_results_csv"], config["office_cluster_id"]
    )
    anchor_travel_minutes = _anchor_travel_minutes(config["origin_summary_csv"])
    best_commute_by_locality = _best_commute_row_per_locality(config["commute_score_csv"])

    anchors_by_locality = {}
    for row in origins:
        if row["cluster_id"] == config["office_cluster_id"]:
            continue
        distance_km = anchor_distances_km.get(row["cluster_id"])
        if distance_km is None:
            continue  # no route data for this anchor -- skip rather than guess
        anchors_by_locality.setdefault(row["locality"], []).append({
            "cluster_id": row["cluster_id"],
            "representative_pocket": row["representative_pocket"],
            "distance_km": distance_km,
        })

    localities = []
    for locality, anchors in anchors_by_locality.items():
        commute_row = best_commute_by_locality.get(locality)
        if commute_row is None:
            continue
        best_departure_time = commute_row["departure_time"]

        enriched_anchors = []
        for anchor in sorted(anchors, key=lambda a: a["distance_km"]):
            travel = anchor_travel_minutes.get((anchor["cluster_id"], best_departure_time))
            if travel is None:
                continue  # no summary data for this anchor at this slot -- skip rather than guess
            enriched_anchors.append({**anchor, **travel})

        localities.append({
            "locality": locality,
            "anchors": enriched_anchors,
            "latest_fully_reliable_departure": commute_row["latest_fully_reliable_departure"],
            "commute_score": float(commute_row["commute_score"]),
        })
    return localities


def annotate_range_status(localities, max_distance_km):
    """ALL localities are returned, never filtered out, and EVERY
    representative anchor of each locality is kept (never collapsed to
    one). Range status is determined independently at two levels, from
    the same road-distance data:

    - Per anchor: within_range = anchor.distance_km <= max_distance_km,
      computed independently for each anchor, so one locality can contain
      both within-range and beyond-range reference points.
    - Per locality (used only to choose which section -- "within
      preferred range" vs. "beyond preferred range" -- the locality is
      grouped under): within_range = True if ANY of its anchors qualify.
    """
    results = []
    for loc in localities:
        anchors = []
        locality_within_range = False
        for anchor in loc["anchors"]:
            anchor_within_range = anchor["distance_km"] <= max_distance_km
            locality_within_range = locality_within_range or anchor_within_range
            anchors.append({**anchor, "within_range": anchor_within_range})

        result = dict(loc)
        result["anchors"] = anchors
        result["within_range"] = locality_within_range
        results.append(result)
    return results
