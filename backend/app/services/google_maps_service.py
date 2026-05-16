import json
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.exceptions.route_errors import RouteUnavailableError
from app.schemas.routes import PlaceInput
from app.services.departure_time_service import is_departure_now, resolve_departure_epoch_seconds

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
_DIRECTIONS_TIMEOUT = httpx.Timeout(25.0, connect=8.0)
_directions_client: httpx.AsyncClient | None = None
_DEBUG_LOG = Path(__file__).resolve().parents[3] / ".cursor" / "debug-ce83c2.log"

_NO_TRANSIT_MESSAGE = (
    "No public transport route was found for this departure time. Try Leave now or a different time."
)


def _agent_log(hypothesis_id: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "ce83c2",
            "hypothesisId": hypothesis_id,
            "location": "google_maps_service.py",
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _DEBUG_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion


def _get_directions_client() -> httpx.AsyncClient:
    global _directions_client
    if _directions_client is None or _directions_client.is_closed:
        _directions_client = httpx.AsyncClient(timeout=_DIRECTIONS_TIMEOUT)
    return _directions_client


@dataclass
class CandidateRoute:
    duration_minutes: int
    walking_distance_meters: int
    transfers: int
    steps: list[dict]
    polyline: str | None
    raw: dict


def candidate_has_transit(candidate: CandidateRoute) -> bool:
    """True when the route includes at least one public-transit leg."""
    return any(step.get("travel_mode") == "TRANSIT" for step in candidate.steps)


def filter_transit_candidates(candidates: list[CandidateRoute]) -> list[CandidateRoute]:
    """Keep only routes that use public transit (exclude walking-only fallbacks)."""
    return [candidate for candidate in candidates if candidate_has_transit(candidate)]


def _is_google_maps_place_id(place_id: str | None) -> bool:
    """Only real Google place IDs are valid for Directions place_id: prefix."""
    if not place_id:
        return False
    lowered = place_id.strip().lower()
    if lowered.startswith(("eldergo:", "station:")):
        return False
    return True


def _place_value(place: PlaceInput) -> str:
    if place.lat is not None and place.lon is not None:
        return f"{place.lat},{place.lon}"
    if _is_google_maps_place_id(place.google_place_id):
        return f"place_id:{place.google_place_id}"
    return place.display_name


def _parse_routes(body: dict) -> list[CandidateRoute]:
    candidates: list[CandidateRoute] = []
    for route in body.get("routes") or []:
        leg = route.get("legs", [{}])[0]
        steps = leg.get("steps", [])
        walking_distance = sum(
            step.get("distance", {}).get("value", 0)
            for step in steps
            if step.get("travel_mode") == "WALKING"
        )
        transfers = sum(1 for step in steps if step.get("travel_mode") == "TRANSIT")
        candidates.append(
            CandidateRoute(
                duration_minutes=max(1, round(leg.get("duration", {}).get("value", 0) / 60)),
                walking_distance_meters=walking_distance,
                transfers=max(0, transfers - 1),
                steps=steps,
                polyline=route.get("overview_polyline", {}).get("points"),
                raw=route,
            )
        )
    return candidates


async def _fetch_directions_candidates(
    origin: PlaceInput,
    destination: PlaceInput,
    departure_time: str,
) -> list[CandidateRoute]:
    """Call Google Directions and parse all routes. Empty list when API has no routes."""
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    params = {
        "origin": _place_value(origin),
        "destination": _place_value(destination),
        "mode": "transit",
        "alternatives": "true",
        "key": settings.google_maps_api_key,
        "language": "en",
        "region": "my",
    }
    if is_departure_now(departure_time):
        params["departure_time"] = "now"
    else:
        params["departure_time"] = resolve_departure_epoch_seconds(departure_time)

    _agent_log(
        "H1",
        "directions_request_start",
        {
            "alternatives": True,
            "origin": params["origin"][:60],
            "destination": params["destination"][:60],
            "departure_epoch": params.get("departure_time"),
        },
    )
    req_started = time.perf_counter()
    client = _get_directions_client()
    response = await client.get(DIRECTIONS_URL, params=params)
    response.raise_for_status()
    body = response.json()
    _agent_log(
        "H1",
        "directions_request_done",
        {
            "ms": round((time.perf_counter() - req_started) * 1000, 1),
            "status": body.get("status"),
            "route_count": len(body.get("routes") or []),
        },
    )

    status = body.get("status")
    if status in {"ZERO_RESULTS", "NOT_FOUND"}:
        return []
    if status != "OK":
        raise HTTPException(status_code=502, detail=f"Google Directions error: {status}")

    return _parse_routes(body)


async def fetch_transit_candidates_lenient(
    origin: PlaceInput,
    destination: PlaceInput,
    departure_time: str,
) -> list[CandidateRoute]:
    """Return transit-only candidates, or [] when none (never raises no_transit_route)."""
    candidates = await _fetch_directions_candidates(origin, destination, departure_time)
    return filter_transit_candidates(candidates)


async def fetch_transit_candidates(
    origin: PlaceInput,
    destination: PlaceInput,
    departure_time: str,
) -> list[CandidateRoute]:
    """Return transit-only candidates; raises RouteUnavailableError when none exist."""
    transit_candidates = await fetch_transit_candidates_lenient(origin, destination, departure_time)
    if not transit_candidates:
        raise RouteUnavailableError(
            "no_transit_route",
            _NO_TRANSIT_MESSAGE,
            departure_time=departure_time,
        )
    return transit_candidates


async def fetch_candidate_routes(
    origin: PlaceInput,
    destination: PlaceInput,
    departure_time: str,
    *,
    preferences=None,
) -> list[CandidateRoute]:
    """Backward-compatible alias for strict transit fetch (preferences ignored)."""
    del preferences
    return await fetch_transit_candidates(origin, destination, departure_time)
