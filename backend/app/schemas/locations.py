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
    routes: list[str] = []


class LocationDetail(LocationSummary):
    # Detail view extends summary with station-specific enrichment fields.
    routes: list[str] = []
    known_facilities: list[str] = []
    source_list: list[str] = []
    # Scraped from mrt.com.my (CSV); optional enrichment for selected hubs.
    station_facilities: list[str] = []
    station_address: str | None = None
    station_hours_summary: str | None = None
    facility_source_url: str | None = None
