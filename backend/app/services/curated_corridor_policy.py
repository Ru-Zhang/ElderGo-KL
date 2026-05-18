"""When backend/data/route_*.csv curated assets apply on Monash corridor trips."""

from __future__ import annotations

import re
from typing import Literal

from app.services.klcc_monash_route_service import (
    is_ss18_stop,
    is_sunu_monash_stop,
    is_usj7_stop,
)

CANONICAL_CORRIDOR_ROUTE_KEY = "klcc|monash university malaysia"

CuratedCorridorProfile = Literal["full", "usj7_brt", "sunu_arrival"]


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


def is_usj7_place(name: str | None) -> bool:
    normalized = _normalize_place(name)
    if not normalized or is_ss18_stop(name):
        return False
    if "usj 7" in normalized or "usj7" in normalized or "usj-7" in normalized:
        return True
    return "usj" in normalized and re.search(r"\b7\b", normalized) is not None


def is_sunu_monash_place(name: str | None) -> bool:
    return is_sunu_monash_stop(name)


def is_monash_place(name: str | None) -> bool:
    if is_sunu_monash_stop(name):
        return False
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


def _step_uses_ss18(step: dict) -> bool:
    if (step.get("travel_mode") or "").upper() != "TRANSIT":
        return False
    transit = step.get("transit_details") or {}
    departure = (transit.get("departure_stop") or {}).get("name") or ""
    arrival = (transit.get("arrival_stop") or {}).get("name") or ""
    return is_ss18_stop(departure) or is_ss18_stop(arrival)


def _has_brt_usj7_to_sunu(steps: list[dict]) -> bool:
    for step in steps:
        if (step.get("travel_mode") or "").upper() != "TRANSIT":
            continue
        transit = step.get("transit_details") or {}
        departure = (transit.get("departure_stop") or {}).get("name") or ""
        arrival = (transit.get("arrival_stop") or {}).get("name") or ""
        vehicle = ((transit.get("line") or {}).get("vehicle") or {}).get("type") or ""
        if vehicle.upper() == "BUS" and is_usj7_stop(departure) and is_sunu_monash_stop(arrival):
            return True
    return False


def google_steps_use_usj7_kjl_brt(steps: list[dict]) -> bool:
    """True when steps include Kelana Jaya LRT to USJ7 and Sunway BRT USJ7 → Sunu-Monash."""
    if not steps:
        return False
    if any(_step_uses_ss18(step) for step in steps):
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

        if vehicle == "SUBWAY" and is_usj7_stop(arrival):
            if is_klcc_place(departure) or "KJ" in line_label or "KELANA" in line_label:
                has_kjl_to_usj7 = True

        if vehicle == "BUS" and is_usj7_stop(departure) and is_sunu_monash_stop(arrival):
            has_brt_usj7_to_sunu = True

    return has_kjl_to_usj7 and has_brt_usj7_to_sunu


def _origin_allows_curated(origin_name: str) -> bool:
    return (
        is_klcc_place(origin_name)
        or is_usj7_place(origin_name)
        or is_sunu_monash_place(origin_name)
    )


def _is_walk_to_monash(step: dict, destination_name: str) -> bool:
    if (step.get("travel_mode") or "").upper() != "WALKING":
        return False
    instruction = _normalize_place(step.get("html_instructions"))
    return is_monash_place(destination_name) and "monash" in instruction


def detect_curated_profile(
    origin_name: str,
    destination_name: str,
    google_steps: list[dict] | None = None,
) -> CuratedCorridorProfile | None:
    """Pick which CSV step numbers (1–5) apply for this Monash-bound trip."""
    if not is_monash_place(destination_name) or is_monash_place(origin_name):
        return None

    if google_steps:
        if any(_step_uses_ss18(step) for step in google_steps):
            return None
        if is_canonical_klcc_to_monash_od(origin_name, destination_name) and google_steps_use_usj7_kjl_brt(
            google_steps
        ):
            return "full"
        if is_sunu_monash_place(origin_name) and not _has_brt_usj7_to_sunu(google_steps):
            return "sunu_arrival"
        # KL Sentral → Monash (and any hub): use steps 3–5 when the route includes USJ7 BRT.
        if _has_brt_usj7_to_sunu(google_steps):
            return "usj7_brt"
        return None

    if not _origin_allows_curated(origin_name):
        return None
    if is_canonical_klcc_to_monash_od(origin_name, destination_name):
        return "full"
    if is_sunu_monash_place(origin_name):
        return "sunu_arrival"
    if is_usj7_place(origin_name):
        return "usj7_brt"
    return None


def should_use_curated_route_csv(
    origin_name: str,
    destination_name: str,
    *,
    google_steps: list[dict] | None = None,
) -> bool:
    return detect_curated_profile(origin_name, destination_name, google_steps=google_steps) is not None


def csv_step_for_google_step(
    step: dict,
    profile: CuratedCorridorProfile,
    *,
    origin_name: str,
    destination_name: str,
) -> int | None:
    """Map a Google Directions step to route_station_images.csv step_number (1–5)."""
    mode = (step.get("travel_mode") or "").upper()
    instruction = _normalize_place(step.get("html_instructions"))

    if profile == "sunu_arrival":
        if _is_walk_to_monash(step, destination_name):
            return 5
        if mode == "TRANSIT":
            transit = step.get("transit_details") or {}
            departure = (transit.get("departure_stop") or {}).get("name") or ""
            arrival = (transit.get("arrival_stop") or {}).get("name") or ""
            if is_sunu_monash_stop(departure) or is_sunu_monash_stop(arrival):
                return 5
        return None

    if profile == "usj7_brt":
        if mode == "WALKING":
            if _is_walk_to_monash(step, destination_name):
                return 5
            if is_usj7_stop(instruction) or is_usj7_place(origin_name):
                return 3
            return None
        if mode == "TRANSIT":
            transit = step.get("transit_details") or {}
            departure = (transit.get("departure_stop") or {}).get("name") or ""
            arrival = (transit.get("arrival_stop") or {}).get("name") or ""
            vehicle = ((transit.get("line") or {}).get("vehicle") or {}).get("type") or ""
            if vehicle.upper() == "SUBWAY" and is_usj7_stop(arrival):
                return 3
            if vehicle.upper() == "BUS" and is_usj7_stop(departure):
                return 4
        return None

    # full — KLCC → USJ7 (KJL) → USJ7 BRT → Monash
    if mode == "WALKING":
        if _is_walk_to_monash(step, destination_name):
            return 5
        if "klcc" in instruction and not is_usj7_stop(instruction):
            return 1
        if is_usj7_stop(instruction) or "usj 7" in instruction or "usj7" in instruction:
            return 3
        return None

    if mode == "TRANSIT":
        transit = step.get("transit_details") or {}
        departure = (transit.get("departure_stop") or {}).get("name") or ""
        arrival = (transit.get("arrival_stop") or {}).get("name") or ""
        vehicle = ((transit.get("line") or {}).get("vehicle") or {}).get("type") or ""
        if vehicle.upper() == "SUBWAY" and is_klcc_place(departure):
            return 2
        if vehicle.upper() == "SUBWAY" and is_usj7_stop(arrival):
            return 3
        if vehicle.upper() == "BUS" and is_usj7_stop(departure):
            return 4

    return None
