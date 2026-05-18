"""Load curated route/station image paths from CSV (no DB migration).

image_path values are served from frontend/public (e.g. /route-images/klcc-monash/...).
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from app.core.paths import ROUTE_STATION_IMAGES_CSV, ROUTE_STATION_IMAGES_LINKED_CSV
from app.services.curated_corridor_policy import is_canonical_corridor_route_key

CSV_PATH = ROUTE_STATION_IMAGES_CSV
LINKED_CSV_PATH = ROUTE_STATION_IMAGES_LINKED_CSV

class RouteStationImage(TypedDict):
    path: str
    caption: str


def _is_valid_image_path(image_path: str) -> bool:
    normalized = image_path.strip().lower()
    return normalized.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))


def _normalize_part(value: str) -> str:
    return " ".join(value.strip().lower().split())


def normalize_route_key(route_key: str) -> str:
    raw = route_key.strip()
    if "|" not in raw:
        return _normalize_part(raw)
    origin, destination = raw.split("|", 1)
    return f"{_normalize_part(origin)}|{_normalize_part(destination)}"


def normalize_station_key(station_key: str) -> str:
    return _normalize_part(station_key)


def _station_lookup_keys(station_key: str) -> list[str]:
    normalized = normalize_station_key(station_key)
    keys = [normalized]
    compact = normalized.replace(" ", "")
    if compact and compact not in keys:
        keys.append(compact)
    return keys


def _resolve_lookup_key(row: dict[str, str | None]) -> str | None:
    """Prefer explicit step_number, then station_key (e.g. step:3 or klcc)."""
    step_raw = (row.get("step_number") or "").strip()
    if step_raw:
        try:
            step_number = int(step_raw)
        except ValueError:
            step_number = 0
        if step_number > 0:
            return f"step:{step_number}"

    station_key = normalize_station_key(row.get("station_key") or "")
    return station_key or None


def _read_csv_grouped(csv_path: Path) -> dict[tuple[str, str], list[tuple[int, RouteStationImage]]]:
    if not csv_path.is_file():
        return {}

    grouped: dict[tuple[str, str], list[tuple[int, RouteStationImage]]] = {}
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            route_key = normalize_route_key(row.get("route_key") or "")
            lookup_key = _resolve_lookup_key(row)
            image_path = (row.get("image_path") or "").strip()
            image_caption = (row.get("image_caption") or "").strip()
            if not route_key or not lookup_key or not _is_valid_image_path(image_path):
                continue
            try:
                image_order = int((row.get("image_order") or "0").strip())
            except ValueError:
                image_order = 0

            bucket = grouped.setdefault((route_key, lookup_key), [])
            bucket.append((image_order, {"path": image_path, "caption": image_caption}))
    return grouped


@lru_cache
def _load_rows() -> dict[tuple[str, str], list[RouteStationImage]]:
    # Primary CSV first; linked CSV overrides rows with complete image paths.
    merged: dict[tuple[str, str], list[tuple[int, RouteStationImage]]] = {}
    for csv_path in (CSV_PATH, LINKED_CSV_PATH):
        grouped = _read_csv_grouped(csv_path)
        for key, items in grouped.items():
            merged[key] = items

    flattened: dict[tuple[str, str], list[RouteStationImage]] = {}
    for key, items in merged.items():
        items.sort(key=lambda item: item[0])
        flattened[key] = [image for _, image in items]
    return flattened


def get_route_station_image_map(route_key: str) -> dict[str, list[RouteStationImage]]:
    normalized_route = normalize_route_key(route_key)
    if not is_canonical_corridor_route_key(normalized_route):
        return {}
    rows = _load_rows()
    result: dict[str, list[RouteStationImage]] = {}
    for (route, station), images in rows.items():
        if route == normalized_route and images:
            result[station] = list(images)
    return result


def get_route_station_images(route_key: str, station_key: str) -> list[RouteStationImage]:
    normalized_route = normalize_route_key(route_key)
    if not is_canonical_corridor_route_key(normalized_route):
        return []
    rows = _load_rows()
    for alias in _station_lookup_keys(station_key):
        images = rows.get((normalized_route, alias))
        if images:
            return list(images)
    return []


def get_route_step_images(route_key: str, step_number: int) -> list[RouteStationImage]:
    if step_number < 1:
        return []
    normalized_route = normalize_route_key(route_key)
    if not is_canonical_corridor_route_key(normalized_route):
        return []
    rows = _load_rows()
    images = rows.get((normalized_route, f"step:{step_number}"))
    return list(images) if images else []


def reload_route_station_images_cache() -> None:
    _load_rows.cache_clear()

