from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.preferences import TravelPreferences


class PlaceInput(BaseModel):
    display_name: str
    lat: float | None = None
    lon: float | None = None
    google_place_id: str | None = None


class RouteRecommendationRequest(BaseModel):
    anonymous_user_id: str | None = None
    origin: PlaceInput
    destination: PlaceInput
    departure_time: str = "now"
    # Default preferences allow recommendation API to work without onboarding payload.
    preferences: TravelPreferences = Field(default_factory=TravelPreferences)


class RouteAccessibilityAnnotation(BaseModel):
    status: Literal["supported", "limited", "unknown", "not_verified", "not_supported"] = "unknown"
    message: str
    source: str


class RouteAccessibilityPoint(BaseModel):
    step_number: int
    point_id: str
    name: str | None = None
    lat: float
    lon: float
    annotation_type: str
    accessibility_type: str | None = None
    wheelchair: str | None = None
    shelter: str | None = None
    covered: str | None = None
    distance_meters: int | None = None


class RouteStep(BaseModel):
    step_number: int
    step_type: Literal["walking", "transit", "arrival"]
    instruction: str
    duration_minutes: int | None = None
    distance_meters: int | None = None
    transit_line: str | None = None
    map_polyline: str | None = None
    transit_color: str | None = None
    transit_vehicle_type: str | None = None
    from_station: str | None = None
    to_station: str | None = None
    annotation: RouteAccessibilityAnnotation


class RecommendedRoute(BaseModel):
    recommended_route_id: str
    origin_name: str
    destination_name: str
    duration_minutes: int
    transfers: int
    walking_distance_meters: int
    recommendation_reason: str
    map_polyline: str | None = None
    steps: list[RouteStep]
    # Accessibility points are optional enrichments extracted from walking segments.
    accessibility_points: list[RouteAccessibilityPoint] = Field(default_factory=list)
