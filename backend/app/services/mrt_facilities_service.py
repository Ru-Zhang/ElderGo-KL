"""Load scraped mrt.com.my station extras from CSV (no DB migration)."""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BACKEND_DIR / "data" / "mrt_stations_facilities.csv"


@lru_cache
def _load_rows() -> dict[str, dict]:
    if not CSV_PATH.is_file():
        return {}

    rows: dict[str, dict] = {}
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            location_id = (row.get("location_id") or "").strip()
            if not location_id:
                continue
            facilities_raw = row.get("facilities_json") or "[]"
            try:
                facilities = json.loads(facilities_raw)
            except json.JSONDecodeError:
                facilities = []
            if not isinstance(facilities, list):
                facilities = []

            facilities_clean = [str(x).strip() for x in facilities if str(x).strip()]
            rows[location_id] = {
                "station_facilities": facilities_clean,
                "station_address": (row.get("address") or "").strip() or None,
                "station_hours_summary": (row.get("hours_summary") or "").strip() or None,
                "facility_source_url": (row.get("source_url") or "").strip() or None,
            }
    return rows


def get_mrt_facilities(location_id: str) -> dict | None:
    data = _load_rows().get(location_id)
    return dict(data) if data else None


def reload_mrt_facilities_cache() -> None:
    _load_rows.cache_clear()
