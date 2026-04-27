import csv
import json
import re
from functools import lru_cache
from pathlib import Path

from app.schemas.locations import LocationDetail, LocationSummary

ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
CSV_ROOT = BACKEND_ROOT / "csv_output"
if not CSV_ROOT.exists():
    CSV_ROOT = ROOT / "data" / "csv_output"

SOURCE_SYSTEM_LABELS = {
    "rapid_rail": "Rapid Rail",
    "ktmb": "KTMB",
}


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


def _canonical_station_name(value: str) -> str:
    value = re.sub(r"\s*-\s*REDONE$", "", value.strip(), flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value)
    return value.upper()


def _station_group_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"station:{slug}"


def _route_name_from_stop(source_system: str, row: dict[str, str], route_names: dict[str, str]) -> str | None:
    route_id = _clean(row.get("route_id"))
    if route_id:
        route_name = route_names.get(route_id)
        if route_name:
            return route_name

    if source_system != "rapid_rail":
        return route_id

    stop_id = _clean(row.get("stop_id")) or ""
    prefix = re.match(r"^[A-Z]+", stop_id)
    prefix_value = prefix.group(0) if prefix else route_id
    return {
        "AG": "AGL",
        "KJ": "KJL",
        "SP": "SPL",
        "KG": "KGL",
        "PY": "PYL",
        "MR": "MRL",
        "BRT": "BRT",
    }.get(prefix_value or "", route_id)


def _load_route_names(folder: str) -> dict[str, str]:
    route_names: dict[str, str] = {}
    routes_path = CSV_ROOT / folder / "routes.csv"
    if not routes_path.exists():
        return route_names

    with routes_path.open("r", encoding="utf-8-sig", newline="") as src:
        for row in csv.DictReader(src):
            route_id = _clean(row.get("route_id"))
            route_name = _clean(row.get("route_short_name")) or _clean(row.get("route_long_name"))
            if route_id and route_name:
                route_names[route_id] = route_name
    return route_names


def _merge_station_status(statuses: list[str]) -> str:
    if "supported" in statuses:
        return "supported"
    if "not_supported" in statuses:
        return "not_supported"
    return "unknown"


def _accessibility_note(status: str) -> str:
    if status == "supported":
        return "Accessibility information is available for this station."
    if status == "not_supported":
        return "No accessibility support is recorded for this station."
    return "Accessibility information is not yet verified for this station."


@lru_cache
def load_csv_locations() -> list[LocationDetail]:
    station_groups: dict[str, dict] = {}

    for source_system, folder in (("ktmb", "ktmb_data"), ("rapid_rail", "rapid_rail_data")):
        stops_path = CSV_ROOT / folder / "stops.csv"
        if not stops_path.exists():
            continue
        route_names = _load_route_names(folder)
        with stops_path.open("r", encoding="utf-8-sig", newline="") as src:
            for row in csv.DictReader(src):
                stop_id = _clean(row.get("stop_id"))
                name = _clean(row.get("stop_name"))
                if not stop_id or not name:
                    continue
                status = "supported" if str(row.get("isOKU", "")).lower() == "true" else "unknown"
                canonical_name = _canonical_station_name(name)
                group_id = _station_group_id(canonical_name)
                group = station_groups.setdefault(
                    group_id,
                    {
                        "name": canonical_name,
                        "lat_values": [],
                        "lon_values": [],
                        "statuses": [],
                        "routes": set(),
                        "source_systems": set(),
                    },
                )
                lat = float(row["stop_lat"]) if _clean(row.get("stop_lat")) else None
                lon = float(row["stop_lon"]) if _clean(row.get("stop_lon")) else None
                if lat is not None:
                    group["lat_values"].append(lat)
                if lon is not None:
                    group["lon_values"].append(lon)
                route_name = _route_name_from_stop(source_system, row, route_names)
                if route_name:
                    group["routes"].add(route_name)
                group["statuses"].append(status)
                group["source_systems"].add(SOURCE_SYSTEM_LABELS.get(source_system, source_system))

    locations: list[LocationDetail] = []
    for group_id, group in station_groups.items():
        status = _merge_station_status(group["statuses"])
        locations.append(
            LocationDetail(
                id=group_id,
                name=group["name"],
                type="rail_station",
                lat=sum(group["lat_values"]) / len(group["lat_values"]) if group["lat_values"] else None,
                lon=sum(group["lon_values"]) / len(group["lon_values"]) if group["lon_values"] else None,
                accessibility_status=status,
                confidence="medium" if status != "unknown" else "unknown",
                note=_accessibility_note(status),
                routes=sorted(group["routes"]),
                known_facilities=[],
                source_list=sorted(group["source_systems"]),
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
