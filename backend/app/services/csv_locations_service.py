import csv
import json
from functools import lru_cache
from pathlib import Path

from app.schemas.locations import LocationDetail, LocationSummary

ROOT = Path(__file__).resolve().parents[3]
CSV_ROOT = ROOT / "data" / "csv_output"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _point_from_wkt(value: str | None) -> tuple[float | None, float | None]:
    if not value or not value.startswith("POINT("):
        return None, None
    try:
        lon_lat = value.removeprefix("POINT(").removesuffix(")").split()
        return float(lon_lat[1]), float(lon_lat[0])
    except (IndexError, ValueError):
        return None, None


def _status_from_wheelchair(value: str | None) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"yes", "true", "1", "limited"}:
        return "supported"
    return "unknown"


@lru_cache
def load_csv_locations() -> list[LocationDetail]:
    locations: list[LocationDetail] = []

    for source_system, folder in (("ktmb", "ktmb_data"), ("rapid_rail", "rapid_rail_data")):
        stops_path = CSV_ROOT / folder / "stops.csv"
        if not stops_path.exists():
            continue
        with stops_path.open("r", encoding="utf-8-sig", newline="") as src:
            for row in csv.DictReader(src):
                stop_id = _clean(row.get("stop_id"))
                name = _clean(row.get("stop_name"))
                if not stop_id or not name:
                    continue
                status = "supported" if str(row.get("isOKU", "")).lower() == "true" else "unknown"
                routes = [row["route_id"]] if _clean(row.get("route_id")) else []
                locations.append(
                    LocationDetail(
                        id=f"{source_system}:{stop_id}",
                        name=name,
                        type="rail_station",
                        lat=float(row["stop_lat"]) if _clean(row.get("stop_lat")) else None,
                        lon=float(row["stop_lon"]) if _clean(row.get("stop_lon")) else None,
                        accessibility_status=status,
                        confidence="medium" if status != "unknown" else "unknown",
                        note="Loaded from data/csv_output. Import PostgreSQL for richer station profiles.",
                        routes=routes,
                        known_facilities=[],
                        source_list=[f"{source_system}:{stop_id}"],
                    )
                )

    accessibility_path = CSV_ROOT / "accessibility_feature_clean.csv"
    if accessibility_path.exists():
        with accessibility_path.open("r", encoding="utf-8-sig", newline="") as src:
            for row in csv.DictReader(src):
                source_id = _clean(row.get("source_id"))
                name = _clean(row.get("name_en")) or _clean(row.get("name_ms")) or _clean(row.get("name_default"))
                if not source_id or not name:
                    continue
                lat, lon = _point_from_wkt(row.get("geom_wkt"))
                raw_properties = []
                try:
                    raw = json.loads(row.get("raw_properties") or "{}")
                    raw_properties = [str(raw.get("@id"))] if raw.get("@id") else []
                except json.JSONDecodeError:
                    raw_properties = []
                status = _status_from_wheelchair(row.get("wheelchair"))
                locations.append(
                    LocationDetail(
                        id=f"osm:{source_id}",
                        name=name,
                        type="accessibility_point",
                        lat=lat,
                        lon=lon,
                        accessibility_status=status,
                        confidence="medium" if status != "unknown" else "unknown",
                        note="Loaded from accessibility_feature_clean.csv.",
                        routes=[],
                        known_facilities=[
                            value
                            for value in [
                                row.get("feature_type"),
                                row.get("accessibility_type"),
                            ]
                            if _clean(value)
                        ],
                        source_list=raw_properties or [source_id],
                    )
                )

    return locations


def popular_csv_locations() -> list[LocationSummary]:
    stations = [location for location in load_csv_locations() if location.type == "rail_station"]
    preferred = ["kl sentral", "pasar seni", "bukit bintang", "ampang", "klcc"]
    stations.sort(
        key=lambda location: next(
            (index for index, name in enumerate(preferred) if name in location.name.lower()),
            len(preferred),
        )
    )
    return [LocationSummary(**location.model_dump()) for location in stations[:8]]


def search_csv_locations(query: str) -> list[LocationSummary]:
    lowered = query.lower()
    matches = [
        location
        for location in load_csv_locations()
        if lowered in location.name.lower()
    ]
    matches.sort(key=lambda location: (not location.name.lower().startswith(lowered), location.name))
    return [LocationSummary(**location.model_dump()) for location in matches[:20]]


def get_csv_location(location_id: str) -> LocationDetail | None:
    return next((location for location in load_csv_locations() if location.id == location_id), None)
