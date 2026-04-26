from fastapi import APIRouter

from app.schemas.places import PlaceDetail, PlaceSuggestion
from app.services.places_service import autocomplete_places, get_place_detail, get_station_place_detail

router = APIRouter()


@router.get("/autocomplete", response_model=list[PlaceSuggestion])
async def autocomplete(q: str) -> list[PlaceSuggestion]:
    if not q.strip():
        return []
    return await autocomplete_places(q)


@router.get("/details/{place_id}", response_model=PlaceDetail)
async def details(place_id: str) -> PlaceDetail:
    return await get_place_detail(place_id)


@router.get("/station-detail", response_model=PlaceDetail)
async def station_detail(name: str, lat: float | None = None, lon: float | None = None) -> PlaceDetail:
    return await get_station_place_detail(name, lat, lon)
