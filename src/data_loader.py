"""Read-only access to the frozen residential origins dataset.

data/residential_origins_FROZEN_v1.csv is approved and frozen: this module
only reads it, and must never write, modify, or regenerate it.
"""

import csv


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_row_by_cluster_id(csv_path, cluster_id):
    for row in load_rows(csv_path):
        if row["cluster_id"] == cluster_id:
            return row
    raise ValueError(f"cluster_id '{cluster_id}' not found in {csv_path}")
