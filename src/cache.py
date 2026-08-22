"""Minimal JSON-file cache for Routes API responses.

Only successful responses are ever cached (callers should not call `set`
after a failed request), so a rerun automatically retries prior failures
while skipping everything that already succeeded.

Key format: "{origin_cluster_id}|{departure_time_iso}"
"""

import json
import os


def load(cache_path):
    if not os.path.exists(cache_path):
        return {}
    with open(cache_path, encoding="utf-8") as f:
        return json.load(f)


def make_key(origin_cluster_id, departure_time_iso):
    return f"{origin_cluster_id}|{departure_time_iso}"


def get(cache, origin_cluster_id, departure_time_iso):
    return cache.get(make_key(origin_cluster_id, departure_time_iso))


def set_and_save(cache, cache_path, origin_cluster_id, departure_time_iso, route):
    cache[make_key(origin_cluster_id, departure_time_iso)] = route
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
