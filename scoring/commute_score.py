"""V1 commute scoring PROTOTYPE.

commute_score = 0.45 * reliability_score + 0.30 * efficiency_score + 0.25 * flexibility_score

Reads data/interim/locality_departure_time_summary.csv (read-only) and
produces data/interim/commute_score_v1.csv (locality x departure_time,
42 rows). This is a commute-only prototype -- no budget, gym, or housing
factors are included, and no localities/origins are ranked against each
other here.

PROTOTYPE ASSUMPTIONS -- not statistically validated, chosen as reasonable
round-number cutoffs for a first pass:
  - Median Score: <=15 min -> 100, >=30 min -> 0, linear in between.
  - P90 Score:    <=20 min -> 100, >=40 min -> 0, linear in between.
These thresholds were not derived from any statistical analysis of what
"good" vs "bad" commute times are -- they are placeholder judgment calls
for V1 and should be revisited before this feeds a real housing decision.

Run from the project root: python scoring/commute_score.py
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUMMARY_CSV = PROJECT_ROOT / "data" / "interim" / "locality_departure_time_summary.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "interim" / "commute_score_v1.csv"

DEPARTURE_TIME_ORDER = ["08:30", "08:45", "09:00", "09:15", "09:30", "09:45", "10:00"]
DEPARTURE_TIME_TO_FLEX_SCORE = {
    "08:30": 0,
    "08:45": 16.67,
    "09:00": 33.33,
    "09:15": 50,
    "09:30": 66.67,
    "09:45": 83.33,
    "10:00": 100,
}

# PROTOTYPE ASSUMPTION -- see module docstring.
MEDIAN_SCORE_LOW_MIN, MEDIAN_SCORE_HIGH_MIN = 15, 30
# PROTOTYPE ASSUMPTION -- see module docstring.
P90_SCORE_LOW_MIN, P90_SCORE_HIGH_MIN = 20, 40

RELIABILITY_WEIGHT = 0.45
EFFICIENCY_WEIGHT = 0.30
FLEXIBILITY_WEIGHT = 0.25
MEDIAN_WEIGHT_WITHIN_EFFICIENCY = 0.70
P90_WEIGHT_WITHIN_EFFICIENCY = 0.30

OUTPUT_FIELDNAMES = [
    "locality",
    "departure_time",
    "median_traffic_duration_minutes",
    "p90_traffic_duration_minutes",
    "on_time_rate",
    "reliability_score",
    "median_score",
    "p90_score",
    "efficiency_score",
    "latest_fully_reliable_departure",
    "flexibility_score",
    "commute_score",
]


def clamp_linear(x, low, high, score_at_low, score_at_high):
    """Linear interpolation between (low -> score_at_low) and (high -> score_at_high),
    clamped at both ends."""
    if x <= low:
        return score_at_low
    if x >= high:
        return score_at_high
    frac = (x - low) / (high - low)
    return score_at_low + frac * (score_at_high - score_at_low)


def load_summary():
    with open(SUMMARY_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_latest_fully_reliable_departure(rows_by_time):
    """Latest (chronologically last) departure_time slot where ALL of the
    locality's representative origins were on time on ALL 5 weekdays
    (weekday_on_time_count == weekday_count). Scans in fixed chronological
    order; does not assume reliability decays monotonically with later
    departure times, even though it does in the current dataset."""
    latest = None
    for t in DEPARTURE_TIME_ORDER:
        row = rows_by_time[t]
        if int(row["weekday_on_time_count"]) == int(row["weekday_count"]):
            latest = t
    return latest


def score_row(row, flexibility_score, latest_fully_reliable_departure):
    on_time_rate = float(row["on_time_count"]) / float(row["sample_size"])
    reliability_score = on_time_rate * 100

    median_min = float(row["median_traffic_duration_seconds"]) / 60
    median_score = clamp_linear(
        median_min, MEDIAN_SCORE_LOW_MIN, MEDIAN_SCORE_HIGH_MIN, 100, 0
    )

    p90_min = float(row["p90_traffic_duration_seconds"]) / 60
    p90_score = clamp_linear(p90_min, P90_SCORE_LOW_MIN, P90_SCORE_HIGH_MIN, 100, 0)

    efficiency_score = (
        MEDIAN_WEIGHT_WITHIN_EFFICIENCY * median_score
        + P90_WEIGHT_WITHIN_EFFICIENCY * p90_score
    )

    commute_score = (
        RELIABILITY_WEIGHT * reliability_score
        + EFFICIENCY_WEIGHT * efficiency_score
        + FLEXIBILITY_WEIGHT * flexibility_score
    )

    return {
        "locality": row["locality"],
        "departure_time": row["departure_time"],
        "median_traffic_duration_minutes": median_min,
        "p90_traffic_duration_minutes": p90_min,
        "on_time_rate": on_time_rate,
        "reliability_score": reliability_score,
        "median_score": median_score,
        "p90_score": p90_score,
        "efficiency_score": efficiency_score,
        "latest_fully_reliable_departure": latest_fully_reliable_departure,
        "flexibility_score": flexibility_score,
        "commute_score": commute_score,
    }


def main():
    rows = load_summary()

    by_locality = defaultdict(dict)
    for r in rows:
        by_locality[r["locality"]][r["departure_time"]] = r

    output_rows = []
    for locality in sorted(by_locality):
        rows_by_time = by_locality[locality]

        latest_fully_reliable_departure = compute_latest_fully_reliable_departure(rows_by_time)
        if latest_fully_reliable_departure is None:
            print(f"WARNING: {locality} has no fully reliable departure-time slot; flexibility_score=0")
            flexibility_score = 0
        else:
            flexibility_score = DEPARTURE_TIME_TO_FLEX_SCORE[latest_fully_reliable_departure]

        for t in DEPARTURE_TIME_ORDER:
            output_rows.append(
                score_row(rows_by_time[t], flexibility_score, latest_fully_reliable_departure)
            )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} rows to {OUTPUT_CSV}")
    print("PROTOTYPE thresholds (median 15/30 min, P90 20/40 min) are documented "
          "assumptions, not statistically validated. See module docstring.")


if __name__ == "__main__":
    main()
