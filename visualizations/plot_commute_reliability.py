"""Two charts from data/interim/locality_departure_time_summary.csv (read-only):

1. Predicted car commute time (median traffic-aware duration) per locality,
   across departure times.
2. Arrival buffer to the 10:20 AM target (median), per locality, across
   departure times, with a 0-minute reference line.

Uses matplotlib's default color cycle -- no manual colors. No scoring or
ranking; this only visualizes the already-approved summary stats.

Run from the project root: python visualizations/plot_commute_reliability.py
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUMMARY_CSV = PROJECT_ROOT / "data" / "interim" / "locality_departure_time_summary.csv"

COMMUTE_TIME_PNG = PROJECT_ROOT / "visualizations" / "predicted_commute_time.png"
ARRIVAL_BUFFER_PNG = PROJECT_ROOT / "visualizations" / "arrival_buffer.png"

DEPARTURE_TIME_ORDER = ["08:30", "08:45", "09:00", "09:15", "09:30", "09:45", "10:00"]


def load_summary():
    with open(SUMMARY_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group_by_locality(rows):
    by_locality = defaultdict(dict)
    for r in rows:
        by_locality[r["locality"]][r["departure_time"]] = r
    return by_locality


def plot_commute_time(by_locality):
    fig, ax = plt.subplots(figsize=(9, 6))

    for locality in sorted(by_locality):
        rows_by_time = by_locality[locality]
        y = [float(rows_by_time[t]["median_traffic_duration_seconds"]) / 60 for t in DEPARTURE_TIME_ORDER]
        ax.plot(DEPARTURE_TIME_ORDER, y, marker="o", linewidth=2, label=locality)

    ax.set_title("Google Traffic-Aware Predicted Car Commute Time\n(median across 5 weekdays, per locality)")
    ax.set_xlabel("Departure time")
    ax.set_ylabel("Median traffic-aware duration (minutes)")
    ax.grid(True, axis="y", color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)
    ax.legend(title="Locality", loc="upper left", bbox_to_anchor=(1.02, 1))

    fig.tight_layout()
    fig.savefig(COMMUTE_TIME_PNG, dpi=150)
    plt.close(fig)


def plot_arrival_buffer(by_locality):
    fig, ax = plt.subplots(figsize=(9, 6))

    for locality in sorted(by_locality):
        rows_by_time = by_locality[locality]
        y = [float(rows_by_time[t]["median_arrival_buffer_minutes"]) for t in DEPARTURE_TIME_ORDER]
        ax.plot(DEPARTURE_TIME_ORDER, y, marker="o", linewidth=2, label=locality)

    ax.axhline(0, color="#898781", linestyle="--", linewidth=1.5)

    ax.set_title("Arrival Buffer to 10:20 AM Target\n(median across 5 weekdays, per locality)")
    ax.set_xlabel("Departure time")
    ax.set_ylabel("Median arrival buffer (minutes)")
    ax.grid(True, axis="y", color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)
    ax.legend(title="Locality", loc="upper left", bbox_to_anchor=(1.02, 1))

    fig.text(
        0.5, -0.02,
        "Positive = predicted arrival before 10:20 AM   |   Negative = predicted arrival after 10:20 AM",
        ha="center", fontsize=9, color="#52514e",
    )

    fig.tight_layout()
    fig.savefig(ARRIVAL_BUFFER_PNG, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    rows = load_summary()
    by_locality = group_by_locality(rows)

    COMMUTE_TIME_PNG.parent.mkdir(parents=True, exist_ok=True)

    plot_commute_time(by_locality)
    plot_arrival_buffer(by_locality)

    print(f"Wrote {COMMUTE_TIME_PNG}")
    print(f"Wrote {ARRIVAL_BUFFER_PNG}")


if __name__ == "__main__":
    main()
