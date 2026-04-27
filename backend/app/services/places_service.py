import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.places import PlaceDetail, PlaceSuggestion

PLACES_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACE_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


async def autocomplete_places(query: str) -> list[PlaceSuggestion]:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    params = {
        "input": query,
        "key": settings.google_maps_api_key,
        "components": "country:my",
        "language": "en",
        "location": "3.1390,101.6869",
        "radius": 70000,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(PLACES_AUTOCOMPLETE_URL, params=params)
        response.raise_for_status()
        body = response.json()

    status = body.get("status")
    if status not in {"OK", "ZERO_RESULTS"}:
        raise HTTPException(status_code=502, detail=f"Google Places error: {status}")

    return [
        PlaceSuggestion(
            description=item["description"],
            place_id=item["place_id"],
            main_text=item.get("structured_formatting", {}).get("main_text"),
            secondary_text=item.get("structured_formatting", {}).get("secondary_text"),
        )
        for item in body.get("predictions", [])
    ]


async def get_place_detail(place_id: str) -> PlaceDetail:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    params = {
        "place_id": place_id,
        "key": settings.google_maps_api_key,
        "fields": (
            "name,formatted_address,geometry,place_id,rating,user_ratings_total,"
            "website,formatted_phone_number,opening_hours"
        ),
        "language": "en",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(PLACE_DETAILS_URL, params=params)
        response.raise_for_status()
        body = response.json()

    if body.get("status") != "OK":
        raise HTTPException(status_code=502, detail=f"Google Place Details error: {body.get('status')}")

    result = body["result"]
    location = result.get("geometry", {}).get("location", {})
    opening_hours = result.get("opening_hours", {}).get("weekday_text", [])
    return PlaceDetail(
        display_name=result.get("formatted_address") or result.get("name") or place_id,
        google_place_id=result.get("place_id") or place_id,
        lat=location.get("lat"),
        lon=location.get("lng"),
        name=result.get("name"),
        formatted_address=result.get("formatted_address"),
        rating=result.get("rating"),
        user_ratings_total=result.get("user_ratings_total"),
        website=result.get("website"),
        phone_number=result.get("formatted_phone_number"),
        opening_hours=opening_hours,
    )


async def get_station_place_detail(name: str, lat: float | None = None, lon: float | None = None) -> PlaceDetail:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    params = {
        "query": f"{name} station Kuala Lumpur Malaysia",
        "key": settings.google_maps_api_key,
        "language": "en",
        "region": "my",
    }
    if lat is not None and lon is not None:
        params["location"] = f"{lat},{lon}"
        params["radius"] = 500

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(PLACE_TEXT_SEARCH_URL, params=params)
        response.raise_for_status()
        body = response.json()

    status = body.get("status")
    if status not in {"OK", "ZERO_RESULTS"}:
        raise HTTPException(status_code=502, detail=f"Google Place Search error: {status}")
    if status == "ZERO_RESULTS" or not body.get("results"):
        raise HTTPException(status_code=404, detail="Google place details were not found for this station.")

    place_id = body["results"][0].get("place_id")
    if not place_id:
        raise HTTPException(status_code=404, detail="Google place details were not found for this station.")
    return await get_place_detail(place_id)
