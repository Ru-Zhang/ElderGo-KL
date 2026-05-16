import re
import time

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.places import PlaceDetail, PlaceSuggestion

_PLACES_HTTP_TIMEOUT = 5.0
_PLACES_SEARCH_CACHE_TTL_SEC = 300.0
_places_client: httpx.AsyncClient | None = None
_search_cache: dict[str, tuple[float, list[PlaceDetail]]] = {}


def _places_http_client() -> httpx.AsyncClient:
    global _places_client
    if _places_client is None or _places_client.is_closed:
        _places_client = httpx.AsyncClient(timeout=_PLACES_HTTP_TIMEOUT)
    return _places_client

PLACES_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACE_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"
STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"

# Google Place types for rail/BRT/LRT/bus stops — exclude generic POIs (restaurants, etc.).
_TRANSIT_STATION_TYPES = frozenset(
    {
        "transit_station",
        "train_station",
        "subway_station",
        "bus_station",
        "light_rail_station",
    }
)

_TRANSIT_TYPE_PRIORITY = (
    "train_station",
    "subway_station",
    "light_rail_station",
    "transit_station",
    "bus_station",
)

_AUTOCOMPLETE_TRANSIT_TYPES = (
    "train_station",
    "transit_station",
    "subway_station",
    "bus_station",
    "light_rail_station",
)


def _normalize_place_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def _format_place_display_name(value: str | None) -> str:
    if not value:
        return ""
    without_brackets = re.sub(r"\s*\([^)]*\)\s*", " ", value)
    without_brackets = re.sub(r"\s{2,}", " ", without_brackets).strip()
    parts = [part.strip() for part in without_brackets.split(",") if part.strip()]
    if not parts:
        return without_brackets
    if len(parts) == 1:
        return parts[0]
    first_part = parts[0]
    if re.search(r"[A-Za-z]", first_part) and not re.fullmatch(r"\d+", first_part):
        return first_part
    second_part = parts[1]
    if second_part and re.search(r"[A-Za-z]", second_part):
        return second_part
    return first_part


def _place_texts_match(a: str, b: str) -> bool:
    return _normalize_place_text(a) == _normalize_place_text(b)


def is_transit_station_types(types: list[str] | None) -> bool:
    if not types:
        return False
    return bool(_TRANSIT_STATION_TYPES.intersection(t.lower() for t in types))


def _transit_type_rank(types: list[str]) -> int:
    normalized = {t.lower() for t in types}
    if not normalized & _TRANSIT_STATION_TYPES:
        return 999
    for index, preferred in enumerate(_TRANSIT_TYPE_PRIORITY):
        if preferred in normalized:
            return index
    return len(_TRANSIT_TYPE_PRIORITY)


def _station_name_loose_match(query: str, display_name: str) -> bool:
    """Allow step labels like USJ7 to match USJ7 LRT Station when resolving transit photos."""
    normalized_query = _normalize_place_text(query)
    normalized_name = _normalize_place_text(display_name)
    if not normalized_query or not normalized_name:
        return False
    if normalized_query == normalized_name:
        return True
    if normalized_name.startswith(f"{normalized_query} "):
        return True
    query_compact = normalized_query.replace(" ", "")
    name_compact = normalized_name.replace(" ", "")
    return bool(query_compact and query_compact in name_compact)


def _suggestion_name_matches(
    query: str,
    suggestion: PlaceSuggestion,
    *,
    loose: bool = False,
) -> bool:
    short = _format_place_display_name(suggestion.main_text or suggestion.description)
    normalized_query = _normalize_place_text(query)
    exact = (
        _place_texts_match(short, query)
        or _place_texts_match(suggestion.description, query)
        or _normalize_place_text(short) == normalized_query
    )
    if exact:
        return True
    if loose:
        return _station_name_loose_match(query, short) or _station_name_loose_match(
            query, suggestion.description
        )
    return False


def pick_autocomplete_place_id(
    name: str,
    suggestions: list[PlaceSuggestion],
    *,
    transit_only: bool = False,
) -> str | None:
    """Match autocomplete results; for stations prefer train/LRT/BRT types over generic POIs."""
    query = name.strip()
    if not query or not suggestions:
        return None

    matches: list[PlaceSuggestion] = []
    for suggestion in suggestions:
        if not _suggestion_name_matches(query, suggestion, loose=transit_only):
            continue
        if transit_only and not is_transit_station_types(suggestion.types):
            continue
        matches.append(suggestion)

    if not matches:
        return None

    matches.sort(key=lambda item: _transit_type_rank(item.types))
    return matches[0].place_id


def _parse_autocomplete_predictions(predictions: list[dict]) -> list[PlaceSuggestion]:
    return [
        PlaceSuggestion(
            description=item["description"],
            place_id=item["place_id"],
            main_text=item.get("structured_formatting", {}).get("main_text"),
            secondary_text=item.get("structured_formatting", {}).get("secondary_text"),
            types=list(item.get("types") or []),
        )
        for item in predictions
    ]


async def _autocomplete_request(query: str, *, place_type: str | None = None) -> list[PlaceSuggestion]:
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
    if place_type:
        params["types"] = place_type

    client = _places_http_client()
    response = await client.get(PLACES_AUTOCOMPLETE_URL, params=params)
    response.raise_for_status()
    body = response.json()

    status = body.get("status")
    if status not in {"OK", "ZERO_RESULTS"}:
        raise HTTPException(status_code=502, detail=f"Google Places error: {status}")

    return _parse_autocomplete_predictions(body.get("predictions", []))


async def autocomplete_places(query: str, *, transit_only: bool = False) -> list[PlaceSuggestion]:
    if not transit_only:
        return await _autocomplete_request(query)

    merged: dict[str, PlaceSuggestion] = {}
    for place_type in _AUTOCOMPLETE_TRANSIT_TYPES:
        for suggestion in await _autocomplete_request(query, place_type=place_type):
            if suggestion.place_id not in merged:
                merged[suggestion.place_id] = suggestion
    return list(merged.values())


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

    client = _places_http_client()
    response = await client.get(PLACE_DETAILS_URL, params=params)
    response.raise_for_status()
    body = response.json()

    if body.get("status") != "OK":
        raise HTTPException(status_code=502, detail=f"Google Place Details error: {body.get('status')}")

    result = body["result"]
    location = result.get("geometry", {}).get("location", {})
    opening_hours = result.get("opening_hours", {}).get("weekday_text", [])
    # Prefer short place name over full formatted address for planning UI readability.
    return PlaceDetail(
        display_name=result.get("name") or result.get("formatted_address") or place_id,
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


async def search_places_kv(query: str, limit: int = 5) -> list[PlaceDetail]:
    """Text-search places biased to Klang Valley; returns up to limit candidates."""
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    cache_key = query.strip().lower()
    now = time.monotonic()
    cached = _search_cache.get(cache_key)
    if cached and now - cached[0] < _PLACES_SEARCH_CACHE_TTL_SEC:
        return cached[1][:limit]

    params = {
        "query": f"{query.strip()}, Malaysia",
        "key": settings.google_maps_api_key,
        "language": "en",
        "region": "my",
        "location": "3.1390,101.6869",
        "radius": 70000,
    }

    client = _places_http_client()
    response = await client.get(PLACE_TEXT_SEARCH_URL, params=params)
    response.raise_for_status()
    body = response.json()

    status = body.get("status")
    if status not in {"OK", "ZERO_RESULTS"}:
        raise HTTPException(status_code=502, detail=f"Google Place Search error: {status}")
    if status == "ZERO_RESULTS" or not body.get("results"):
        return []

    places: list[PlaceDetail] = []
    for item in body.get("results", [])[:limit]:
        place_id = item.get("place_id")
        if not place_id:
            continue
        location = item.get("geometry", {}).get("location", {})
        places.append(
            PlaceDetail(
                display_name=item.get("name") or item.get("formatted_address") or query,
                google_place_id=place_id,
                lat=location.get("lat"),
                lon=location.get("lng"),
                name=item.get("name"),
                formatted_address=item.get("formatted_address"),
            )
        )
    _search_cache[cache_key] = (now, places)
    return places


async def _search_station_place_id_text(name: str, lat: float | None = None, lon: float | None = None) -> str:
    settings = get_settings()
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

    transit_results = [
        item
        for item in body.get("results", [])
        if is_transit_station_types(item.get("types"))
    ]
    if not transit_results:
        raise HTTPException(status_code=404, detail="Google place details were not found for this station.")

    transit_results.sort(key=lambda item: _transit_type_rank(list(item.get("types") or [])))
    place_id = transit_results[0].get("place_id")
    if not place_id:
        raise HTTPException(status_code=404, detail="Google place details were not found for this station.")
    return place_id


async def _search_station_place_id(name: str, lat: float | None = None, lon: float | None = None) -> str:
    settings = get_settings()
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="Google Maps API key is not configured.")

    # Station images: restrict to train/LRT/BRT/bus stop place types only.
    try:
        suggestions = await autocomplete_places(name.strip(), transit_only=True)
        place_id = pick_autocomplete_place_id(name, suggestions, transit_only=True)
        if place_id:
            return place_id
    except HTTPException:
        pass

    return await _search_station_place_id_text(name, lat, lon)


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
        "fields": "photos,types,name",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        detail_response = await client.get(PLACE_DETAILS_URL, params=detail_params)
        detail_response.raise_for_status()
        detail_body = detail_response.json()

        if detail_body.get("status") != "OK":
            raise HTTPException(
                status_code=502, detail=f"Google Place Details error: {detail_body.get('status')}"
            )

        result = detail_body.get("result", {})
        place_types = list(result.get("types") or [])
        if not is_transit_station_types(place_types):
            return await get_station_static_map_image(name, lat, lon)

        # Google details may not include photos for every station/place.
        photos = result.get("photos", [])
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
