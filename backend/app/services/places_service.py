import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.places import PlaceDetail, PlaceSuggestion

PLACES_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACE_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"
STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"


async def autocomplete_places(query: str) -> list[PlaceSuggestion]:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    params = {
        "input": query,
        "key": settings.google_maps_api_key,
        "components": "country:my",
        "language": "en",
        # Bias autocomplete near KL to reduce irrelevant out-of-region suggestions.
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


async def _search_station_place_id(name: str, lat: float | None = None, lon: float | None = None) -> str:
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
        # Tight radius improves disambiguation for station names with duplicates.
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
    return place_id


async def get_station_place_detail(name: str, lat: float | None = None, lon: float | None = None) -> PlaceDetail:
    place_id = await _search_station_place_id(name, lat, lon)
    return await get_place_detail(place_id)


async def get_station_static_map_image(
    name: str, lat: float | None = None, lon: float | None = None
) -> tuple[bytes, str]:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    # Prefer exact coordinates when available; otherwise use text center fallback.
    center = f"{lat},{lon}" if lat is not None and lon is not None else f"{name} station Kuala Lumpur Malaysia"
    params = {
        "center": center,
        "zoom": 16 if lat is not None and lon is not None else 14,
        "size": "1280x720",
        "scale": 2,
        "maptype": "roadmap",
        "key": settings.google_maps_api_key,
    }
    if lat is not None and lon is not None:
        params["markers"] = f"color:0x1a73e8|{lat},{lon}"
    else:
        params["markers"] = f"color:0x1a73e8|{center}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(STATIC_MAP_URL, params=params)
        response.raise_for_status()

    content_type = response.headers.get("content-type", "image/png")
    return response.content, content_type


async def get_station_photo_image(
    name: str, lat: float | None = None, lon: float | None = None
) -> tuple[bytes, str]:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    place_id = await _search_station_place_id(name, lat, lon)
    detail_params = {
        "place_id": place_id,
        "key": settings.google_maps_api_key,
        "fields": "photos",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        detail_response = await client.get(PLACE_DETAILS_URL, params=detail_params)
        detail_response.raise_for_status()
        detail_body = detail_response.json()

        if detail_body.get("status") != "OK":
            raise HTTPException(
                status_code=502, detail=f"Google Place Details error: {detail_body.get('status')}"
            )

        # Google details may not include photos for every station/place.
        photos = detail_body.get("result", {}).get("photos", [])
        if photos:
            photo_reference = photos[0].get("photo_reference")
            if photo_reference:
                photo_params = {
                    "photo_reference": photo_reference,
                    "maxwidth": 1280,
                    "key": settings.google_maps_api_key,
                }
                photo_response = await client.get(PLACE_PHOTO_URL, params=photo_params)
                photo_response.raise_for_status()
                content_type = photo_response.headers.get("content-type", "image/jpeg")
                return photo_response.content, content_type

    # If no photo is available, keep UX stable with static map fallback.
    return await get_station_static_map_image(name, lat, lon)
