from fastapi import APIRouter, Response

from app.schemas.places import PlaceDetail, PlaceSuggestion
from app.services.places_service import (
    autocomplete_places,
    get_place_detail,
    get_station_photo_image,
    get_station_place_detail,
)
from app.services.curated_corridor_policy import is_canonical_corridor_route_key
from app.services.route_station_images_service import (
    get_route_station_image_map,
    get_route_station_images,
    get_route_step_images,
    normalize_route_key,
    normalize_station_key,
)

router = APIRouter()


@router.get("/autocomplete", response_model=list[PlaceSuggestion])
async def autocomplete(q: str) -> list[PlaceSuggestion]:
    # Short-circuit empty query to avoid unnecessary third-party API calls.
    if not q.strip():
        return []
    return await autocomplete_places(q)


@router.get("/details/{place_id}", response_model=PlaceDetail)
async def details(place_id: str) -> PlaceDetail:
    return await get_place_detail(place_id)


@router.get("/station-detail", response_model=PlaceDetail)
async def station_detail(name: str, lat: float | None = None, lon: float | None = None) -> PlaceDetail:
    return await get_station_place_detail(name, lat, lon)


@router.get("/route-station-images")
async def route_station_images(
    route_key: str,
    station_key: str | None = None,
    step_number: int | None = None,
) -> dict[str, list[dict[str, str]]]:
    if not is_canonical_corridor_route_key(normalize_route_key(route_key)):
        return {}
    if step_number is not None:
        paths = get_route_step_images(route_key, step_number)
        return {f"step:{step_number}": paths} if paths else {}
    if station_key:
        paths = get_route_station_images(route_key, station_key)
        return {normalize_station_key(station_key): paths} if paths else {}
    return get_route_station_image_map(route_key)


@router.get("/station-image")
async def station_image(name: str, lat: float | None = None, lon: float | None = None) -> Response:
    # Return raw bytes with upstream content type so frontend can render image
    # directly without additional proxy transformation.
    image_bytes, content_type = await get_station_photo_image(name, lat, lon)
    return Response(content=image_bytes, media_type=content_type)
