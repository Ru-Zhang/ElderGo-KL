from typing import Literal

from pydantic import BaseModel


AccessibilityStatus = Literal["supported", "not_supported", "unknown"]


class LocationSummary(BaseModel):
    id: str
    name: str
    type: str = "rail_station"
    lat: float | None = None
    lon: float | None = None
    accessibility_status: AccessibilityStatus = "unknown"
    confidence: Literal["high", "medium", "low", "unknown"] = "unknown"
    note: str | None = None


class LocationDetail(LocationSummary):
    # Detail view extends summary with station-specific enrichment fields.
    routes: list[str] = []
    known_facilities: list[str] = []
    source_list: list[str] = []
