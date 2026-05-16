from dataclasses import dataclass, field
from typing import Any

from app.schemas.routes import RouteAccessibilityAnnotation, RouteAccessibilityPoint
from app.services.database import get_connection

SUPPORTED_GOOGLE_ACCESSIBILITY_KEYS = {
    "wheelchair_accessible",
    "wheelchair_accessibility",
    "wheelchair_boarding",
    "accessible",
    "accessibility",
    "supports_wheelchair",
}

SUPPORTED_GOOGLE_ACCESSIBILITY_VALUES = {
    "true",
    "yes",
    "supported",
    "available",
    "accessible",
    "wheelchair_accessible",
}

ACCESSIBILITY_SUPPORT_TYPES = {
    "lift",
    "accessible_entrance",
    "kerb_ramp",
    "wheelchair_access",
    "wheelchair_stop",
}


@dataclass
class StationMatch:
    station_id: str
    station_name: str
    accessibility_status: str
    confidence: str
    source_list: list[str] = field(default_factory=list)
    note: str | None = None
    distance_m: float | None = None


@dataclass
class AccessibilityAnnotationResult:
    annotation: RouteAccessibilityAnnotation
    annotation_type: str
    confidence: str = "low"
    target_type: str = "google_hint"
    target_id: str | None = None
    distance_m: int | None = None
    from_station_id: str | None = None
    to_station_id: str | None = None
    start_wkt: str | None = None
    end_wkt: str | None = None
    path_wkt: str | None = None
    accessibility_point: RouteAccessibilityPoint | None = None


def unknown_annotation(message: str, source: str = "no_verified_local_data") -> RouteAccessibilityAnnotation:
    return RouteAccessibilityAnnotation(status="unknown", message=message, source=source)


def _point_wkt(location: dict[str, Any] | None) -> str | None:
    if not location:
        return None
    lat = location.get("lat")
    lon = location.get("lng", location.get("lon"))
    if lat is None or lon is None:
        return None
    return f"POINT({lon} {lat})"


def _decode_google_polyline(encoded: str | None) -> list[tuple[float, float]]:
    if not encoded:
        return []

    coords: list[tuple[float, float]] = []
    index = 0
    lat = 0
    lng = 0

    # Decode Google encoded polyline into (lat, lon) pairs.
    while index < len(encoded):
        result = 0
        shift = 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        delta_lat = ~(result >> 1) if result & 1 else result >> 1
        lat += delta_lat

        result = 0
        shift = 0
        while True:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        delta_lng = ~(result >> 1) if result & 1 else result >> 1
        lng += delta_lng

        coords.append((lat / 1e5, lng / 1e5))

    return coords


def _line_wkt_from_step(google_step: dict[str, Any]) -> str | None:
    coords = _decode_google_polyline(google_step.get("polyline", {}).get("points"))
    if len(coords) < 2:
        # Some steps do not include a decodable polyline; fallback to a straight
        # segment from start/end so spatial lookups still work.
        start = google_step.get("start_location")
        end = google_step.get("end_location")
        if start and end:
            start_lat = start.get("lat")
            start_lon = start.get("lng", start.get("lon"))
            end_lat = end.get("lat")
            end_lon = end.get("lng", end.get("lon"))
            if None not in (start_lat, start_lon, end_lat, end_lon):
                coords = [(start_lat, start_lon), (end_lat, end_lon)]
    if len(coords) < 2:
        return None
    points = ", ".join(f"{lon} {lat}" for lat, lon in coords)
    return f"LINESTRING({points})"


def _google_has_accessibility_hint(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_normalized = str(key).lower()
            if key_normalized in SUPPORTED_GOOGLE_ACCESSIBILITY_KEYS:
                if isinstance(nested, bool) and nested:
                    return True
                if isinstance(nested, str) and nested.lower() in SUPPORTED_GOOGLE_ACCESSIBILITY_VALUES:
                    return True
            if _google_has_accessibility_hint(nested):
                return True
    elif isinstance(value, list):
        return any(_google_has_accessibility_hint(item) for item in value)
    return False


def _source_from_profile(row: StationMatch) -> str:
    if row.source_list:
        return ",".join(row.source_list)
    return "station_accessibility_profiles"


def _station_message(row: StationMatch) -> str:
    if row.accessibility_status == "supported":
        return f"{row.station_name} has verified accessibility support."
    if row.accessibility_status == "not_supported":
        return f"{row.station_name} does not have verified accessibility support."
    return f"No verified accessibility support profile found for {row.station_name}."


def _normalize_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _stop_cache_key(stop: dict[str, Any]) -> str:
    location = stop.get("location", {})
    lat = location.get("lat")
    lon = location.get("lng", location.get("lon"))
    if lat is not None and lon is not None:
        return f"coord:{round(float(lat), 5)},{round(float(lon), 5)}"
    name = stop.get("name")
    if name:
        return f"name:{str(name).strip().lower()}"
    return "unknown"


def _row_to_station_match(row) -> StationMatch:
    return StationMatch(
        station_id=row["station_id"],
        station_name=row["station_name"],
        accessibility_status=row["accessibility_status"],
        confidence=row["confidence"],
        source_list=_normalize_json_list(row["source_list"]),
        note=row["note"],
        distance_m=row["distance_m"],
    )


def _find_station_by_coordinate_with_conn(
    conn,
    lat: float | None,
    lon: float | None,
) -> StationMatch | None:
    if lat is None or lon is None:
        return None
    row = conn.execute(
            """
            SELECT
                station.station_id,
                station.station_name,
                COALESCE(profile.accessibility_status, 'unknown') AS accessibility_status,
                COALESCE(profile.confidence, 'low') AS confidence,
                COALESCE(profile.source_list, '[]'::jsonb) AS source_list,
                profile.note,
                ST_Distance(
                    station.geom::geography,
                    ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography
                ) AS distance_m
            FROM rail_stations station
            LEFT JOIN station_accessibility_profiles profile
              ON profile.station_id = station.station_id
            WHERE station.geom IS NOT NULL
              AND ST_DWithin(
                station.geom::geography,
                ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography,
                100
              )
            ORDER BY distance_m ASC
            LIMIT 1
            """,
            {"lat": lat, "lon": lon},
        ).fetchone()
    if not row:
        return None
    return _row_to_station_match(row)


def _find_station_by_coordinate(lat: float | None, lon: float | None) -> StationMatch | None:
    with get_connection() as conn:
        return _find_station_by_coordinate_with_conn(conn, lat, lon)


def _find_station_by_name_with_conn(conn, name: str | None) -> StationMatch | None:
    if not name:
        return None
    row = conn.execute(
            """
            SELECT
                station.station_id,
                station.station_name,
                COALESCE(profile.accessibility_status, 'unknown') AS accessibility_status,
                COALESCE(profile.confidence, 'low') AS confidence,
                COALESCE(profile.source_list, '[]'::jsonb) AS source_list,
                profile.note,
                NULL::double precision AS distance_m
            FROM rail_stations station
            LEFT JOIN station_accessibility_profiles profile
              ON profile.station_id = station.station_id
            WHERE station.station_name ILIKE %(name_like)s
               OR similarity(station.station_name, %(name)s) > 0.35
            ORDER BY similarity(station.station_name, %(name)s) DESC
            LIMIT 1
            """,
            {"name": name, "name_like": f"%{name}%"},
        ).fetchone()
    if not row:
        return None
    return _row_to_station_match(row)


def _find_station_by_name(name: str | None) -> StationMatch | None:
    with get_connection() as conn:
        return _find_station_by_name_with_conn(conn, name)


def _collect_pending_stops(steps: list[dict[str, Any]]) -> tuple[dict[str, StationMatch | None], list[tuple[str, dict[str, Any]]]]:
    pending: list[tuple[str, dict[str, Any]]] = []
    cache: dict[str, StationMatch | None] = {}
    for step in steps:
        if step.get("travel_mode") != "TRANSIT":
            continue
        transit = step.get("transit_details", {})
        for stop in (transit.get("departure_stop"), transit.get("arrival_stop")):
            if not stop:
                continue
            key = _stop_cache_key(stop)
            if key not in cache:
                cache[key] = None
                pending.append((key, stop))
    return cache, pending


def _prefetch_stations_with_conn(
    conn,
    pending: list[tuple[str, dict[str, Any]]],
    cache: dict[str, StationMatch | None],
) -> None:
    for key, stop in pending:
        location = stop.get("location", {})
        lat = location.get("lat")
        lon = location.get("lng", location.get("lon"))
        matched = _find_station_by_coordinate_with_conn(conn, lat, lon)
        if matched is None:
            matched = _find_station_by_name_with_conn(conn, stop.get("name"))
        cache[key] = matched


def prefetch_station_matches(steps: list[dict[str, Any]]) -> dict[str, StationMatch | None]:
    """Resolve transit stops in one DB connection for a whole route."""
    cache, pending = _collect_pending_stops(steps)
    if not pending:
        return cache

    try:
        with get_connection() as conn:
            _prefetch_stations_with_conn(conn, pending, cache)
    except Exception:
        pass
    return cache


def prefetch_station_matches_with_conn(
    conn,
    steps: list[dict[str, Any]],
) -> dict[str, StationMatch | None]:
    cache, pending = _collect_pending_stops(steps)
    if pending:
        _prefetch_stations_with_conn(conn, pending, cache)
    return cache


def _find_station(
    stop: dict[str, Any] | None,
    station_cache: dict[str, StationMatch | None] | None = None,
) -> StationMatch | None:
    if not stop:
        return None
    if station_cache is not None:
        key = _stop_cache_key(stop)
        if key in station_cache:
            return station_cache[key]
    location = stop.get("location", {})
    lat = location.get("lat")
    lon = location.get("lng", location.get("lon"))
    return _find_station_by_coordinate(lat, lon) or _find_station_by_name(stop.get("name"))


def _walking_accessibility_result_with_conn(conn, path_wkt: str) -> dict[str, Any] | None:
    row = conn.execute(
            """
            SELECT
                accessibility_point_id,
                name,
                accessibility_type,
                wheelchair,
                shelter,
                covered,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon,
                ST_Distance(
                    geom::geography,
                    ST_GeomFromText(%(path_wkt)s, 4326)::geography
                ) AS distance_m
            FROM accessibility_points
            WHERE geom IS NOT NULL
              AND ST_DWithin(
                geom::geography,
                ST_GeomFromText(%(path_wkt)s, 4326)::geography,
                50
              )
            ORDER BY
                CASE
                    -- Rank sheltered points first for elderly comfort, then
                    -- explicit accessibility support, then nearest fallback.
                    WHEN LOWER(COALESCE(shelter, '')) = 'yes'
                      OR LOWER(COALESCE(covered, '')) = 'yes' THEN 0
                    WHEN LOWER(COALESCE(wheelchair, '')) = 'yes'
                      OR LOWER(COALESCE(accessibility_type, '')) = ANY(%(support_types)s::text[]) THEN 1
                    ELSE 2
                END,
                distance_m ASC
            LIMIT 1
            """,
            {"path_wkt": path_wkt, "support_types": list(ACCESSIBILITY_SUPPORT_TYPES)},
        ).fetchone()
    if not row:
        return None

    distance_m = round(row["distance_m"]) if row["distance_m"] is not None else None
    label = row["name"] or row["accessibility_type"] or "Accessibility point"
    if str(row["shelter"] or "").lower() == "yes" or str(row["covered"] or "").lower() == "yes":
        return {
            "annotation_type": "nearby_sheltered_point",
            "point_id": row["accessibility_point_id"],
            "message": f"Covered waiting area nearby: {label}.",
            "distance_m": distance_m,
            "name": label,
            "lat": row["lat"],
            "lon": row["lon"],
            "accessibility_type": row["accessibility_type"],
            "wheelchair": row["wheelchair"],
            "shelter": row["shelter"],
            "covered": row["covered"],
        }
    if (
        str(row["wheelchair"] or "").lower() == "yes"
        or str(row["accessibility_type"] or "").lower() in ACCESSIBILITY_SUPPORT_TYPES
    ):
        return {
            "annotation_type": "nearby_accessibility_support",
            "point_id": row["accessibility_point_id"],
            "message": f"Accessible support nearby: {label}. Ask station staff for help if needed.",
            "distance_m": distance_m,
            "name": label,
            "lat": row["lat"],
            "lon": row["lon"],
            "accessibility_type": row["accessibility_type"],
            "wheelchair": row["wheelchair"],
            "shelter": row["shelter"],
            "covered": row["covered"],
        }
    return None


def _walking_accessibility_result(path_wkt: str) -> dict[str, Any] | None:
    try:
        with get_connection() as conn:
            return _walking_accessibility_result_with_conn(conn, path_wkt)
    except Exception:
        return None


def annotate_all_route_steps(steps: list[dict[str, Any]]) -> list[AccessibilityAnnotationResult]:
    """Prefetch stations and annotate every step using one DB connection."""
    try:
        with get_connection() as conn:
            cache = prefetch_station_matches_with_conn(conn, steps)
            return [
                annotate_google_step(step, station_cache=cache, db_conn=conn) for step in steps
            ]
    except Exception:
        return [annotate_google_step(step) for step in steps]


def quick_step_accessibility_risk(google_step: dict[str, Any]) -> tuple[bool, bool]:
    """Lightweight risk flags for route scoring (no database I/O)."""
    travel_mode = google_step.get("travel_mode")
    if travel_mode == "TRANSIT":
        transit_details = google_step.get("transit_details", {})
        if _google_has_accessibility_hint(transit_details):
            return False, False
        return True, False
    if travel_mode == "WALKING":
        return True, False
    return False, False


def annotate_google_step(
    google_step: dict[str, Any],
    *,
    station_cache: dict[str, StationMatch | None] | None = None,
    db_conn=None,
) -> AccessibilityAnnotationResult:
    start_wkt = _point_wkt(google_step.get("start_location"))
    end_wkt = _point_wkt(google_step.get("end_location"))
    path_wkt = _line_wkt_from_step(google_step)
    travel_mode = google_step.get("travel_mode")

    if travel_mode == "TRANSIT":
        transit_details = google_step.get("transit_details", {})
        departure_stop = transit_details.get("departure_stop")
        arrival_stop = transit_details.get("arrival_stop")
        if _google_has_accessibility_hint(transit_details):
            stop_name = (departure_stop or arrival_stop or {}).get("name")
            return AccessibilityAnnotationResult(
                annotation=RouteAccessibilityAnnotation(
                    status="supported",
                    message="Google Maps indicates accessibility support for this transit step.",
                    source="google_accessibility_hint",
                ),
                annotation_type="station_wheelchair_accessibility",
                confidence="medium",
                target_type="google_transit_step",
                target_id=stop_name,
                start_wkt=start_wkt,
                end_wkt=end_wkt,
                path_wkt=path_wkt,
            )

        # Database lookups are best-effort; annotation generation should never
        # hard-fail route planning.
        try:
            from_station = _find_station(departure_stop, station_cache)
            to_station = _find_station(arrival_stop, station_cache)
        except Exception:
            from_station = None
            to_station = None

        matched = from_station or to_station
        if matched:
            source = _source_from_profile(matched)
            return AccessibilityAnnotationResult(
                annotation=RouteAccessibilityAnnotation(
                    status=matched.accessibility_status,
                    message=_station_message(matched),
                    source=source,
                ),
                annotation_type="station_wheelchair_accessibility",
                confidence=matched.confidence,
                target_type="rail_station",
                target_id=matched.station_id,
                distance_m=round(matched.distance_m) if matched.distance_m is not None else None,
                from_station_id=from_station.station_id if from_station else None,
                to_station_id=to_station.station_id if to_station else None,
                start_wkt=start_wkt,
                end_wkt=end_wkt,
                path_wkt=path_wkt,
            )

        return AccessibilityAnnotationResult(
            annotation=unknown_annotation(
                "No verified local station accessibility profile matched this transit step.",
                "no_verified_local_station_profile",
            ),
            annotation_type="station_wheelchair_accessibility",
            target_type="google_transit_step",
            target_id=(departure_stop or arrival_stop or {}).get("name"),
            start_wkt=start_wkt,
            end_wkt=end_wkt,
            path_wkt=path_wkt,
        )

    if travel_mode == "WALKING":
        if path_wkt:
            # Nearby-point annotation is optional enrichment and should degrade
            # gracefully if spatial data is unavailable.
            try:
                if db_conn is not None:
                    walking_result = _walking_accessibility_result_with_conn(db_conn, path_wkt)
                else:
                    walking_result = _walking_accessibility_result(path_wkt)
            except Exception:
                walking_result = None
            if walking_result:
                annotation_type = walking_result["annotation_type"]
                point_id = walking_result["point_id"]
                return AccessibilityAnnotationResult(
                    annotation=RouteAccessibilityAnnotation(
                        status="supported",
                        message=walking_result["message"],
                        source="accessibility_points",
                    ),
                    annotation_type=annotation_type,
                    confidence="medium",
                    target_type="accessibility_point",
                    target_id=point_id,
                    distance_m=walking_result["distance_m"],
                    start_wkt=start_wkt,
                    end_wkt=end_wkt,
                    path_wkt=path_wkt,
                    accessibility_point=RouteAccessibilityPoint(
                        step_number=0,
                        point_id=point_id,
                        name=walking_result["name"],
                        lat=walking_result["lat"],
                        lon=walking_result["lon"],
                        annotation_type=annotation_type,
                        accessibility_type=walking_result["accessibility_type"],
                        wheelchair=walking_result["wheelchair"],
                        shelter=walking_result["shelter"],
                        covered=walking_result["covered"],
                        distance_meters=walking_result["distance_m"],
                    ),
                )

        return AccessibilityAnnotationResult(
            annotation=unknown_annotation(
                "No verified accessibility information found for this walking part. Please take extra care.",
                "no_nearby_static_accessibility_data",
            ),
            annotation_type="nearby_accessibility_support",
            target_type="walking_segment",
            start_wkt=start_wkt,
            end_wkt=end_wkt,
            path_wkt=path_wkt,
        )

    return AccessibilityAnnotationResult(
        annotation=unknown_annotation(
            "No verified accessibility data found for this route step.",
            "no_verified_route_step_data",
        ),
        annotation_type="accessibility_unknown",
        start_wkt=start_wkt,
        end_wkt=end_wkt,
        path_wkt=path_wkt,
    )
