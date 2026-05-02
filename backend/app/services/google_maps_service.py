from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.routes import PlaceInput

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


@dataclass
class CandidateRoute:
    duration_minutes: int
    walking_distance_meters: int
    transfers: int
    steps: list[dict]
    polyline: str | None
    raw: dict


def _place_value(place: PlaceInput) -> str:
    # Prefer coordinates/place_id over free text to improve Directions accuracy
    # and reduce ambiguous place resolution.
    if place.lat is not None and place.lon is not None:
        return f"{place.lat},{place.lon}"
    if place.google_place_id:
        return f"place_id:{place.google_place_id}"
    return place.display_name


async def fetch_candidate_routes(origin: PlaceInput, destination: PlaceInput, departure_time: str) -> list[CandidateRoute]:
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
    if departure_time == "now":
        params["departure_time"] = "now"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(DIRECTIONS_URL, params=params)
        response.raise_for_status()
        body = response.json()

    status = body.get("status")
    if status != "OK":
        raise HTTPException(status_code=502, detail=f"Google Directions error: {status}")

    candidates: list[CandidateRoute] = []
    for route in body.get("routes", []):
        leg = route.get("legs", [{}])[0]
        steps = leg.get("steps", [])
        walking_distance = sum(
            step.get("distance", {}).get("value", 0)
            for step in steps
            if step.get("travel_mode") == "WALKING"
        )
        # Number of transit legs minus one gives transfer count.
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
