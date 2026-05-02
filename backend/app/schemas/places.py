from pydantic import BaseModel


class PlaceSuggestion(BaseModel):
    description: str
    place_id: str
    main_text: str | None = None
    secondary_text: str | None = None


class PlaceDetail(BaseModel):
    display_name: str
    google_place_id: str
    # Coordinates can be missing when upstream provider does not return geometry.
    lat: float | None = None
    lon: float | None = None
    name: str | None = None
    formatted_address: str | None = None
    rating: float | None = None
    user_ratings_total: int | None = None
    website: str | None = None
    phone_number: str | None = None
    opening_hours: list[str] = []
