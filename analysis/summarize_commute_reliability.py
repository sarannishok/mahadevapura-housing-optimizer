"""Commute-reliability descriptive summary: Level 1 (origin x departure_time)
and Level 2 (locality x departure_time, pooled across each locality's 3
representative origins).

Purely descriptive aggregation of the frozen multiday batch results
(data/interim/batch_traffic_results_multiday.csv, read-only). No scoring,
weighting, or ranking of origins/localities happens here.

Run from the project root: python analysis/summarize_commute_reliability.py
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_loader import load_rows  # noqa: E402

RAW_MULTIDAY_CSV = PROJECT_ROOT / "data" / "interim" / "batch_traffic_results_multiday.csv"
FROZEN_ORIGINS_CSV = PROJECT_ROOT / "data" / "residential_origins_FROZEN_v1.csv"

ORIGIN_OUTPUT_CSV = PROJECT_ROOT / "data" / "interim" / "origin_departure_time_summary.csv"
LOCALITY_OUTPUT_CSV = PROJECT_ROOT / "data" / "interim" / "locality_departure_time_summary.csv"

ORIGIN_FIELDNAMES = [
    "origin_cluster_id",
    "locality",
    "departure_time",
    "sample_size",
    "mean_traffic_duration_seconds",
    "median_traffic_duration_seconds",
    "p90_traffic_duration_seconds",
    "min_traffic_duration_seconds",
    "max_traffic_duration_seconds",
    "mean_arrival_buffer_minutes",
    "median_arrival_buffer_minutes",
    "worst_arrival_buffer_minutes",
    "on_time_count",
    "off_time_count",
]

LOCALITY_FIELDNAMES = [
    "locality",
    "departure_time",
    "sample_size",
    "mean_traffic_duration_seconds",
    "median_traffic_duration_seconds",
    "p90_traffic_duration_seconds",
    "min_traffic_duration_seconds",
    "max_traffic_duration_seconds",
    "mean_arrival_buffer_minutes",
    "median_arrival_buffer_minutes",
    "worst_arrival_buffer_minutes",
    "on_time_count",
    "off_time_count",
    "weekday_on_time_count",
    "weekday_count",
]


def percentile(values, p):
    """Linear interpolation between order statistics (numpy 'linear' method)."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    rank = (p / 100) * (n - 1)
    lower = int(rank)
    upper = min(lower + 1, n - 1)
    frac = rank - lower
    return sorted_vals[lower] + frac * (sorted_vals[upper] - sorted_vals[lower])


def mean(values):
    return sum(values) / len(values)


def median(values):
    return percentile(values, 50)


def load_successful_rows():
    """Read the raw multiday CSV read-only and keep only status == success rows."""
    rows = load_rows(RAW_MULTIDAY_CSV)
    successful = []
    for r in rows:
        if r["status"] != "success":
            continue
        r = dict(r)
        r["traffic_duration_seconds"] = float(r["traffic_duration_seconds"])
        r["arrival_buffer_minutes"] = float(r["arrival_buffer_minutes"])
        successful.append(r)
    return successful


def summarize_group(rows):
    durations = [r["traffic_duration_seconds"] for r in rows]
    buffers = [r["arrival_buffer_minutes"] for r in rows]
    on_time = sum(1 for b in buffers if b >= 0)
    return {
        "sample_size": len(rows),
        "mean_traffic_duration_seconds": mean(durations),
        "median_traffic_duration_seconds": median(durations),
        "p90_traffic_duration_seconds": percentile(durations, 90),
        "min_traffic_duration_seconds": min(durations),
        "max_traffic_duration_seconds": max(durations),
        "mean_arrival_buffer_minutes": mean(buffers),
        "median_arrival_buffer_minutes": median(buffers),
        "worst_arrival_buffer_minutes": min(buffers),
        "on_time_count": on_time,
        "off_time_count": len(rows) - on_time,
    }


def build_origin_summary(rows):
    """Level 1: origin x departure_time, n=5 weekdays per group."""
    groups = defaultdict(list)
    locality_by_origin = {}
    for r in rows:
        key = (r["origin_cluster_id"], r["departure_time"])
        groups[key].append(r)
        locality_by_origin[r["origin_cluster_id"]] = r["locality"]

    output_rows = []
    for (origin_cluster_id, departure_time), group_rows in sorted(groups.items()):
        stats = summarize_group(group_rows)
        output_rows.append({
            "origin_cluster_id": origin_cluster_id,
            "locality": locality_by_origin[origin_cluster_id],
            "departure_time": departure_time,
            **stats,
        })
    return output_rows


def build_locality_summary(rows, locality_to_origins):
    """Level 2: locality x departure_time, pooled n=15 origin-weekday rows per group."""
    groups = defaultdict(list)
    for r in rows:
        key = (r["locality"], r["departure_time"])
        groups[key].append(r)

    output_rows = []
    for (locality, departure_time), group_rows in sorted(groups.items()):
        stats = summarize_group(group_rows)

        # weekday_on_time_count: a weekday counts only if ALL of the
        # locality's representative origins were on time that day.
        by_date = defaultdict(dict)  # date -> {origin_cluster_id: on_time bool}
        for r in group_rows:
            by_date[r["departure_date"]][r["origin_cluster_id"]] = r["arrival_buffer_minutes"] >= 0

        expected_origins = set(locality_to_origins[locality])
        weekday_count = len(by_date)
        weekday_on_time_count = 0
        for date, origin_status in by_date.items():
            if set(origin_status.keys()) >= expected_origins and all(
                origin_status[o] for o in expected_origins
            ):
                weekday_on_time_count += 1

        output_rows.append({
            "locality": locality,
            "departure_time": departure_time,
            **stats,
            "weekday_on_time_count": weekday_on_time_count,
            "weekday_count": weekday_count,
        })
    return output_rows


def main():
    rows = load_successful_rows()

    frozen_rows = load_rows(FROZEN_ORIGINS_CSV)
    locality_to_origins = defaultdict(set)
    for r in frozen_rows:
        if r["cluster_id"] == "OFFICE":
            continue
        locality_to_origins[r["locality"]].add(r["cluster_id"])

    origin_summary = build_origin_summary(rows)
    locality_summary = build_locality_summary(rows, locality_to_origins)

    ORIGIN_OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(ORIGIN_OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ORIGIN_FIELDNAMES)
        writer.writeheader()
        writer.writerows(origin_summary)

    with open(LOCALITY_OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOCALITY_FIELDNAMES)
        writer.writeheader()
        writer.writerows(locality_summary)

    print(f"Wrote {len(origin_summary)} rows to {ORIGIN_OUTPUT_CSV}")
    print(f"Wrote {len(locality_summary)} rows to {LOCALITY_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
