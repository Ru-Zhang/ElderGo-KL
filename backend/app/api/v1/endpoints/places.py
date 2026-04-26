from fastapi import APIRouter

from app.schemas.places import PlaceDetail, PlaceSuggestion
from app.services.places_service import autocomplete_places, get_place_detail

router = APIRouter()


@router.get("/autocomplete", response_model=list[PlaceSuggestion])
async def autocomplete(q: str) -> list[PlaceSuggestion]:
    if not q.strip():
        return []
    return await autocomplete_places(q)


@router.get("/details/{place_id}", response_model=PlaceDetail)
async def details(place_id: str) -> PlaceDetail:
    return await get_place_detail(place_id)
