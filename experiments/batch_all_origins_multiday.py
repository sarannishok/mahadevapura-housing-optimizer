"""Batch traffic-aware WEEKDAY PREDICTION experiment, extended to 5
representative weekdays: all 18 frozen residential origins x OFFICE,
across 7 morning departure times, across 5 dates (config: departure_dates).

This is a traffic-aware prediction dataset (Google's model for what
traffic will look like at each specified future departure time), NOT a
log of historically observed traffic. No scoring, ranking, or dashboard
logic here -- this only collects and flattens raw route data.

Shares data/interim/routes_cache.json with the Monday-only experiment
(experiments/batch_all_origins.py). The cache key already encodes origin +
date + time (origin_cluster_id|departure_time_iso), so Monday's 126
already-cached combinations are reused here with zero API calls -- only
Tuesday-Friday need fresh requests. The Monday-only output CSV
(data/interim/batch_traffic_results.csv) is never read or written by this
script.

Run from the project root: python experiments/batch_all_origins_multiday.py
"""

import argparse
import csv
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cache  # noqa: E402
import time_utils  # noqa: E402
from data_loader import load_rows  # noqa: E402
from routes_client import RoutesAPIError, compute_route  # noqa: E402

OUTPUT_FIELDNAMES = [
    "departure_date",
    "origin_cluster_id",
    "locality",
    "departure_time",
    "destination_cluster_id",
    "distance_meters",
    "static_duration_seconds",
    "traffic_duration_seconds",
    "predicted_arrival_time",
    "arrival_buffer_minutes",
    "status",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-day batch traffic-aware weekday prediction experiment "
        "(18 origins x OFFICE x 5 dates x 7 departure times)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned run (counts, cache-hit vs. needs-fetch breakdown) "
        "without calling the API, touching the cache, or writing the output CSV.",
    )
    return parser.parse_args()


def build_departure_time_iso(departure_date, hhmm, timezone_offset):
    return f"{departure_date}T{hhmm}:00{timezone_offset}"


def row_from_route(origin, departure_date, hhmm, departure_time_iso, target_arrival_iso, route, status):
    distance_meters = route.get("distanceMeters") if route else None
    static_duration_seconds = (
        time_utils.parse_duration_seconds(route["staticDuration"])
        if route and route.get("staticDuration")
        else None
    )
    traffic_duration_seconds = (
        time_utils.parse_duration_seconds(route["duration"])
        if route and route.get("duration")
        else None
    )

    predicted_arrival_time = None
    arrival_buffer_minutes = None
    if traffic_duration_seconds is not None:
        predicted_arrival_time = time_utils.compute_predicted_arrival(
            departure_time_iso, traffic_duration_seconds
        )
        arrival_buffer_minutes = time_utils.compute_arrival_buffer_minutes(
            predicted_arrival_time, target_arrival_iso
        )

    return {
        "departure_date": departure_date,
        "origin_cluster_id": origin["cluster_id"],
        "locality": origin["locality"],
        "departure_time": hhmm,
        "destination_cluster_id": "OFFICE",
        "distance_meters": distance_meters,
        "static_duration_seconds": static_duration_seconds,
        "traffic_duration_seconds": traffic_duration_seconds,
        "predicted_arrival_time": predicted_arrival_time,
        "arrival_buffer_minutes": arrival_buffer_minutes,
        "status": status,
    }


def main():
    args = parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    with open(PROJECT_ROOT / "config" / "batch_config_multiday.yaml") as f:
        config = yaml.safe_load(f)

    csv_path = PROJECT_ROOT / config["origins_csv_path"]
    cache_path = PROJECT_ROOT / config["cache_path"]
    output_csv_path = PROJECT_ROOT / config["output_csv_path"]

    all_rows = load_rows(csv_path)
    office = next(r for r in all_rows if r["cluster_id"] == config["office_cluster_id"])
    origins = [r for r in all_rows if r["cluster_id"] != config["office_cluster_id"]]

    if len(origins) != 18:
        raise SystemExit(
            f"Expected exactly 18 residential origins after excluding OFFICE, "
            f"found {len(origins)} in {csv_path}. Aborting before any API calls."
        )

    departure_dates = config["departure_dates"]
    departure_times = config["departure_times"]
    total = len(departure_dates) * len(origins) * len(departure_times)

    result_cache = cache.load(cache_path)

    if args.dry_run:
        cache_hits = 0
        needs_fetch = 0
        per_date_hits = {d: 0 for d in departure_dates}
        for departure_date in departure_dates:
            for origin in origins:
                for hhmm in departure_times:
                    departure_time_iso = build_departure_time_iso(
                        departure_date, hhmm, config["timezone_offset"]
                    )
                    if cache.get(result_cache, origin["cluster_id"], departure_time_iso) is not None:
                        cache_hits += 1
                        per_date_hits[departure_date] += 1
                    else:
                        needs_fetch += 1

        print("DRY RUN -- no API calls, no cache writes, no output file written.\n")
        print(f"Departure dates: {len(departure_dates)} ({', '.join(departure_dates)})")
        print(f"Residential origins: {len(origins)}")
        print(f"Departure times: {len(departure_times)} ({', '.join(departure_times)})")
        print(f"Total combinations: {total}")
        print(f"Already cached (no call needed): {cache_hits}")
        print(f"Would require new API calls: {needs_fetch}\n")
        print("Cache hits per date:")
        for d, count in per_date_hits.items():
            print(f"  {d}: {count}/{len(origins) * len(departure_times)}")
        return

    output_rows = []
    done = 0

    for departure_date in departure_dates:
        target_arrival_iso = build_departure_time_iso(
            departure_date, config["arrival_target_time"], config["timezone_offset"]
        )

        for origin in origins:
            for hhmm in departure_times:
                done += 1
                departure_time_iso = build_departure_time_iso(
                    departure_date, hhmm, config["timezone_offset"]
                )

                cached_route = cache.get(result_cache, origin["cluster_id"], departure_time_iso)
                if cached_route is not None:
                    print(f"[{done}/{total}] {origin['cluster_id']} @ {departure_date} {hhmm} -- cache hit")
                    output_rows.append(
                        row_from_route(
                            origin, departure_date, hhmm, departure_time_iso,
                            target_arrival_iso, cached_route, "success",
                        )
                    )
                    continue

                try:
                    route = compute_route(
                        origin_lat=float(origin["latitude"]),
                        origin_lng=float(origin["longitude"]),
                        dest_lat=float(office["latitude"]),
                        dest_lng=float(office["longitude"]),
                        departure_time_iso=departure_time_iso,
                        traffic_model=config["traffic_model"],
                    )
                except RoutesAPIError as e:
                    print(f"[{done}/{total}] {origin['cluster_id']} @ {departure_date} {hhmm} -- ERROR: {e}")
                    output_rows.append(
                        row_from_route(
                            origin, departure_date, hhmm, departure_time_iso,
                            target_arrival_iso, None, "error",
                        )
                    )
                    continue

                print(f"[{done}/{total}] {origin['cluster_id']} @ {departure_date} {hhmm} -- fetched")
                cache.set_and_save(result_cache, cache_path, origin["cluster_id"], departure_time_iso, route)
                output_rows.append(
                    row_from_route(
                        origin, departure_date, hhmm, departure_time_iso,
                        target_arrival_iso, route, "success",
                    )
                )

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    success_count = sum(1 for r in output_rows if r["status"] == "success")
    error_count = sum(1 for r in output_rows if r["status"] == "error")
    print(f"\nDone. {success_count} success, {error_count} error. Written to {output_csv_path}")


if __name__ == "__main__":
    main()
