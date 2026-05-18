"""When backend/data/route_*.csv curated assets apply (KLCC → Monash via USJ7 KJL+BRT only)."""

from __future__ import annotations

import re

from app.services.klcc_monash_route_service import (
    is_ss18_stop,
    is_sunu_monash_stop,
    is_usj7_stop,
)
CANONICAL_CORRIDOR_ROUTE_KEY = "klcc|monash university malaysia"


def _normalize_place(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip().lower())


def is_klcc_place(name: str | None) -> bool:
    normalized = _normalize_place(name)
    if not normalized:
        return False
    if normalized == "klcc":
        return True
    if normalized.startswith("klcc "):
        return True
    if "klcc lrt" in normalized or "lrt klcc" in normalized:
        return True
    if "suria" in normalized and "klcc" in normalized:
        return True
    return False


def is_monash_place(name: str | None) -> bool:
    return "monash" in _normalize_place(name)


def is_canonical_klcc_to_monash_od(origin_name: str, destination_name: str) -> bool:
    """Outbound KLCC → Monash only (not Monash → KLCC or other hubs)."""
    return (
        is_klcc_place(origin_name)
        and is_monash_place(destination_name)
        and not is_monash_place(origin_name)
    )


def canonical_route_key_for_od(origin_name: str, destination_name: str) -> str | None:
    if is_canonical_klcc_to_monash_od(origin_name, destination_name):
        return CANONICAL_CORRIDOR_ROUTE_KEY
    return None


def is_canonical_corridor_route_key(route_key: str) -> bool:
    raw = route_key.strip()
    if "|" not in raw:
        return False
    origin, destination = raw.split("|", 1)
    normalized = f"{_normalize_place(origin)}|{_normalize_place(destination)}"
    return normalized == CANONICAL_CORRIDOR_ROUTE_KEY


def google_steps_use_usj7_kjl_brt(steps: list[dict]) -> bool:
    """True when steps include Kelana Jaya LRT to USJ7 and Sunway BRT USJ7 → Sunu-Monash."""
    if not steps:
        return False

    has_kjl_to_usj7 = False
    has_brt_usj7_to_sunu = False

    for step in steps:
        if (step.get("travel_mode") or "").upper() != "TRANSIT":
            continue
        transit = step.get("transit_details") or {}
        departure = (transit.get("departure_stop") or {}).get("name") or ""
        arrival = (transit.get("arrival_stop") or {}).get("name") or ""
        line = transit.get("line") or {}
        vehicle = ((line.get("vehicle") or {}).get("type") or "").upper()
        line_label = f"{line.get('short_name') or ''} {line.get('name') or ''}".upper()

        if is_ss18_stop(departure) or is_ss18_stop(arrival):
            return False

        if vehicle == "SUBWAY" and is_usj7_stop(arrival):
            if is_klcc_place(departure) or "KJ" in line_label or "KELANA" in line_label:
                has_kjl_to_usj7 = True

        if vehicle == "BUS" and is_usj7_stop(departure) and is_sunu_monash_stop(arrival):
            has_brt_usj7_to_sunu = True

    return has_kjl_to_usj7 and has_brt_usj7_to_sunu


def should_use_curated_route_csv(
    origin_name: str,
    destination_name: str,
    *,
    google_steps: list[dict] | None = None,
) -> bool:
    if not is_canonical_klcc_to_monash_od(origin_name, destination_name):
        return False
    if google_steps is None:
        return True
    return google_steps_use_usj7_kjl_brt(google_steps)
