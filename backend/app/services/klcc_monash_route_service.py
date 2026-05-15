"""Compose KLCC → Monash via USJ7 LRT + Sunway BRT (Google omits BRT on single request)."""

from __future__ import annotations

from app.schemas.routes import PlaceInput
from app.services.google_maps_service import CandidateRoute, fetch_candidate_routes

USJ7_INTERCHANGE = PlaceInput(display_name="USJ 7 (KJ31)", lat=3.0553, lon=101.5919)
SUNU_MONASH_BRT = PlaceInput(display_name="SunU-Monash", lat=3.0654, lon=101.6016)


def is_klcc_to_monash_route(origin: PlaceInput, destination: PlaceInput) -> bool:
    origin_text = origin.display_name.lower()
    destination_text = destination.display_name.lower()
    return "klcc" in origin_text and "monash" in destination_text


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


def _pick_brt_candidate(candidates: list[CandidateRoute]) -> CandidateRoute | None:
    for candidate in candidates:
        for step in candidate.steps:
            if step.get("travel_mode") != "TRANSIT":
                continue
            line = step.get("transit_details", {}).get("line", {})
            vehicle_type = line.get("vehicle", {}).get("type")
            line_name = (line.get("name") or line.get("short_name") or "").upper()
            if vehicle_type == "BUS" and "BRT" in line_name:
                return candidate
    return candidates[0] if candidates else None


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


async def fetch_klcc_monash_brt_candidate(
    origin: PlaceInput,
    destination: PlaceInput,
    departure_time: str,
) -> CandidateRoute | None:
    leg1_candidates = await fetch_candidate_routes(origin, USJ7_INTERCHANGE, departure_time)
    leg2_candidates = await fetch_candidate_routes(USJ7_INTERCHANGE, SUNU_MONASH_BRT, departure_time)
    leg3_candidates = await fetch_candidate_routes(SUNU_MONASH_BRT, destination, departure_time)

    if not leg1_candidates or not leg2_candidates or not leg3_candidates:
        return None

    leg1 = leg1_candidates[0]
    leg2 = _pick_brt_candidate(leg2_candidates)
    leg3 = leg3_candidates[0]
    if leg2 is None:
        return None

    return _merge_candidates(leg1, leg2, leg3)


def summarize_candidate(candidate: CandidateRoute) -> dict:
    return {
        "steps": len(candidate.steps),
        "transfers": candidate.transfers,
        "duration_minutes": candidate.duration_minutes,
        "walking_distance_meters": candidate.walking_distance_meters,
        "step_summary": _candidate_step_summary(candidate),
    }
