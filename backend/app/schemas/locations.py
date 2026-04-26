from typing import Literal

from pydantic import BaseModel


AccessibilityStatus = Literal["supported", "limited", "unknown", "not_verified"]


class LocationSummary(BaseModel):
    id: str
    name: str
    type: Literal["rail_station", "accessibility_point", "place"] = "rail_station"
    lat: float | None = None
    lon: float | None = None
    accessibility_status: AccessibilityStatus = "unknown"
    confidence: Literal["high", "medium", "low", "unknown"] = "unknown"
    note: str | None = None


class LocationDetail(LocationSummary):
    routes: list[str] = []
    known_facilities: list[str] = []
    source_list: list[str] = []
