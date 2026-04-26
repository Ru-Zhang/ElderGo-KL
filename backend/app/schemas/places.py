from pydantic import BaseModel


class PlaceSuggestion(BaseModel):
    description: str
    place_id: str
    main_text: str | None = None
    secondary_text: str | None = None


class PlaceDetail(BaseModel):
    display_name: str
    google_place_id: str
    lat: float | None = None
    lon: float | None = None
