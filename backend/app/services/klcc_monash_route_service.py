"""Compose trips to Monash via USJ7 LRT + Sunway BRT (Google omits BRT on single request)."""

from __future__ import annotations

import math
import re

from app.schemas.routes import PlaceInput
from app.services.departure_time_service import departure_iso_after
from app.services.google_maps_service import (
    CandidateRoute,
    fetch_transit_candidates_lenient,
)
from app.services.route_scoring_service import choose_best_candidate

# Integrated USJ7 LRT + BRT hub (Kelana Jaya line → Sunway BRT).
USJ7_INTERCHANGE = PlaceInput(display_name="USJ 7", lat=3.054888, lon=101.59188)
USJ7_BRT_STOP = PlaceInput(display_name="Stesen BRT USJ 7", lat=3.054888, lon=101.59188)
SUNU_MONASH_BRT = PlaceInput(display_name="Stesen BRT Sunu-Monash", lat=3.0654, lon=101.6016)
_NEAR_USJ7_METERS = 500


def is_monash_brt_route(origin: PlaceInput, destination: PlaceInput) -> bool:
    """Monash University trips need USJ7 LRT + Sunway BRT — Google omits BRT on one request."""
    return "monash" in destination.display_name.lower()


def is_klcc_to_monash_route(origin: PlaceInput, destination: PlaceInput) -> bool:
    return is_monash_brt_route(origin, destination)


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _origin_near_usj7(origin: PlaceInput) -> bool:
    if "usj" in origin.display_name.lower():
        return True
    if (
        origin.lat is not None
        and origin.lon is not None
        and USJ7_INTERCHANGE.lat is not None
        and USJ7_INTERCHANGE.lon is not None
    ):
        return (
            _haversine_meters(origin.lat, origin.lon, USJ7_INTERCHANGE.lat, USJ7_INTERCHANGE.lon)
            < _NEAR_USJ7_METERS
        )
    return False


def _leg_duration_seconds(leg: CandidateRoute) -> int:
    return sum(step.get("duration", {}).get("value", 0) for step in leg.steps)


def _candidate_step_summary(candidate: CandidateRoute) -> list[dict]:
    summary: list[dict] = []
    for step in candidate.steps:
        if step.get("travel_mode") == "TRANSIT":
            transit = step.get("transit_details", {})
            line = transit.get("line", {})
            summary.append(
                {
                    "mode": "transit",
                    "vehicle": line.get("vehicle", {}).get("type"),
                    "line": line.get("short_name") or line.get("name"),
                    "from": transit.get("departure_stop", {}).get("name"),
                    "to": transit.get("arrival_stop", {}).get("name"),
                }
            )
        else:
            summary.append({"mode": "walking", "instruction": (step.get("html_instructions") or "")[:80]})
    return summary


def _normalize_stop(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip().lower())


def _stop_matches(name: str | None, *tokens: str) -> bool:
    normalized = _normalize_stop(name)
    return any(token in normalized for token in tokens)


def is_usj7_stop(name: str | None) -> bool:
    normalized = _normalize_stop(name)
    if _stop_matches(name, "ss18", "ss 18"):
        return False
    return _stop_matches(name, "usj 7", "usj7", "usj-7") or (
        "usj" in normalized and re.search(r"\b7\b", normalized) is not None
    )


def is_ss18_stop(name: str | None) -> bool:
    return _stop_matches(name, "ss18", "ss 18")


def is_sunu_monash_stop(name: str | None) -> bool:
    normalized = _normalize_stop(name)
    return "sunu" in normalized or ("sun" in normalized and "monash" in normalized)


def _transit_steps(candidate: CandidateRoute) -> list[dict]:
    return [step for step in candidate.steps if step.get("travel_mode") == "TRANSIT"]


def _transit_stop_names(step: dict) -> tuple[str, str]:
    transit = step.get("transit_details", {})
    departure = transit.get("departure_stop", {}).get("name") or ""
    arrival = transit.get("arrival_stop", {}).get("name") or ""
    return departure, arrival


def _is_brt_step(step: dict) -> bool:
    line = step.get("transit_details", {}).get("line", {})
    vehicle_type = line.get("vehicle", {}).get("type")
    line_name = (line.get("name") or line.get("short_name") or "").upper()
    return vehicle_type == "BUS" and "BRT" in line_name


def _candidate_arrives_at_usj7_lrt(candidate: CandidateRoute) -> bool:
    transit_steps = _transit_steps(candidate)
    if not transit_steps:
        return False
    last_arrival = _transit_stop_names(transit_steps[-1])[1]
    if not is_usj7_stop(last_arrival):
        return False
    for step in transit_steps:
        _, arrival = _transit_stop_names(step)
        if is_ss18_stop(arrival) and not is_usj7_stop(arrival):
            return False
    return True


def _candidate_brt_usj7_to_sunu(candidate: CandidateRoute) -> bool:
    for step in _transit_steps(candidate):
        if not _is_brt_step(step):
            continue
        departure, arrival = _transit_stop_names(step)
        if is_usj7_stop(departure) and is_sunu_monash_stop(arrival):
            return True
    return False


def _pick_brt_candidate(candidates: list[CandidateRoute]) -> CandidateRoute | None:
    corridor = [c for c in candidates if _candidate_brt_usj7_to_sunu(c)]
    pool = corridor or candidates
    for candidate in pool:
        for step in candidate.steps:
            if step.get("travel_mode") != "TRANSIT":
                continue
            if _is_brt_step(step):
                departure, _ = _transit_stop_names(step)
                if corridor or not is_ss18_stop(departure):
                    return candidate
    return None


def _pick_klcc_to_usj7_lrt(candidates: list[CandidateRoute]) -> CandidateRoute | None:
    matching = [c for c in candidates if _candidate_arrives_at_usj7_lrt(c)]
    if not matching:
        return None
    return choose_best_candidate(
        matching,
        accessibility_first=False,
        least_walk=False,
        fewest_transfers=True,
    )


def _pick_usj7_to_sunu_brt(candidates: list[CandidateRoute]) -> CandidateRoute | None:
    matching = [c for c in candidates if _candidate_brt_usj7_to_sunu(c)]
    if matching:
        return choose_best_candidate(
            matching,
            accessibility_first=False,
            least_walk=False,
            fewest_transfers=False,
        )
    brt = _pick_brt_candidate(candidates)
    if brt is not None:
        return brt
    return None


def _merge_candidates(*parts: CandidateRoute) -> CandidateRoute:
    steps: list[dict] = []
    for part in parts:
        steps.extend(part.steps)

    walking_distance = sum(
        step.get("distance", {}).get("value", 0)
        for step in steps
        if step.get("travel_mode") == "WALKING"
    )
    transit_legs = sum(1 for step in steps if step.get("travel_mode") == "TRANSIT")
    duration_seconds = sum(step.get("duration", {}).get("value", 0) for step in steps)

    return CandidateRoute(
        duration_minutes=max(1, round(duration_seconds / 60)),
        walking_distance_meters=walking_distance,
        transfers=max(0, transit_legs - 1),
        steps=steps,
        polyline=parts[0].polyline,
        raw={"composed": True, "segments": [part.raw for part in parts]},
    )


def _pick_leg_neutral(
    candidates: list[CandidateRoute],
    *,
    prefer_brt: bool = False,
) -> CandidateRoute | None:
    if not candidates:
        return None
    if prefer_brt:
        brt = _pick_brt_candidate(candidates)
        if brt is not None:
            return brt
    return choose_best_candidate(
        candidates,
        accessibility_first=False,
        least_walk=False,
        fewest_transfers=False,
    )


async def fetch_klcc_monash_brt_candidate(
    origin: PlaceInput,
    destination: PlaceInput,
    departure_time: str,
) -> CandidateRoute | None:
    """Build a Monash corridor route with chained departures; preferences applied later."""
    parts: list[CandidateRoute] = []
    offset_seconds = 0
    leg_departure = departure_time

    if not _origin_near_usj7(origin):
        leg1_candidates = await fetch_transit_candidates_lenient(
            origin, USJ7_INTERCHANGE, leg_departure
        )
        leg1 = _pick_klcc_to_usj7_lrt(leg1_candidates)
        if leg1 is None:
            return None
        parts.append(leg1)
        offset_seconds += _leg_duration_seconds(leg1)
        leg_departure = departure_iso_after(departure_time, offset_seconds)

    leg2_candidates = await fetch_transit_candidates_lenient(
        USJ7_BRT_STOP, SUNU_MONASH_BRT, leg_departure
    )
    leg2 = _pick_usj7_to_sunu_brt(leg2_candidates)
    if leg2 is None:
        return None
    parts.append(leg2)
    offset_seconds += _leg_duration_seconds(leg2)
    leg_departure = departure_iso_after(departure_time, offset_seconds)

    leg3_candidates = await fetch_transit_candidates_lenient(
        SUNU_MONASH_BRT, destination, leg_departure
    )
    leg3 = _pick_leg_neutral(leg3_candidates)
    if leg3 is None:
        return None
    parts.append(leg3)

    return _merge_candidates(*parts)


def summarize_candidate(candidate: CandidateRoute) -> dict:
    return {
        "steps": len(candidate.steps),
        "transfers": candidate.transfers,
        "duration_minutes": candidate.duration_minutes,
        "walking_distance_meters": candidate.walking_distance_meters,
        "step_summary": _candidate_step_summary(candidate),
    }
