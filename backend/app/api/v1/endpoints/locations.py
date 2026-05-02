import logging
import re

from fastapi import APIRouter, HTTPException

from app.schemas.locations import LocationDetail, LocationSummary
from app.services.csv_locations_service import get_csv_location
from app.services.database import get_connection

router = APIRouter()
logger = logging.getLogger(__name__)


SOURCE_SYSTEM_LABELS = {
    "rapid_rail": "Rapid Rail",
    "ktmb": "KTMB",
}
SOURCE_SYSTEM_ORDER = {
    "Rapid Rail": 0,
    "KTMB": 1,
}


def _canonical_station_name(value: str) -> str:
    normalized = re.sub(r"\s*[-–—]?\s*REDONE$", "", value.strip(), flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"(?<=[A-Z])\s+(?=\d)", "", normalized.upper())
    return normalized.upper()


def _dedupe_location_rows(rows: list[dict], limit: int) -> list[dict]:
    deduped: list[dict] = []
    seen_ids: set[str] = set()
    seen_station_names: set[str] = set()

    for row in rows:
        location_id = str(row["location_id"])
        if location_id in seen_ids:
            continue
        seen_ids.add(location_id)

        # Rail stations may appear multiple times across merged source systems.
        # We collapse them by canonicalized display name for search/popular lists.
        if row.get("location_type") == "rail_station":
            canonical_name = _canonical_station_name(str(row["display_name"]))
            if canonical_name in seen_station_names:
                continue
            seen_station_names.add(canonical_name)

        deduped.append(row)
        if len(deduped) >= limit:
            break

    return deduped


def _location_summary(row: dict) -> LocationSummary:
    return LocationSummary(
        id=row["location_id"],
        name=row["display_name"],
        type=row["location_type"],
        lat=row.get("lat"),
        lon=row.get("lon"),
        accessibility_status=row.get("accessibility_status") or "unknown",
        confidence=row.get("confidence") or "unknown",
        note=None,
    )


def _accessibility_note(status: str) -> str:
    if status == "supported":
        return "Accessibility information is available for this station."
    if status == "not_supported":
        return "No accessibility support is recorded for this station."
    return "Accessibility information is not yet verified for this station."


def _supported_facilities(row: dict, status: str) -> list[str]:
    labels: list[str] = []
    facility_checks = [
        ("wheelchair_access", "Wheelchair access"),
        ("shelter", "Shelter"),
        ("covered", "Covered walkway"),
        ("tactile_paving", "Tactile paving"),
        ("bench", "Bench"),
        ("kerb", "Kerb ramp"),
    ]

    for key, label in facility_checks:
        if row.get(key):
            labels.append(label)

    if status == "supported" and "Wheelchair access" not in labels:
        labels.insert(0, "Wheelchair access")

    return labels


@router.get("/popular", response_model=list[LocationSummary])
def popular_locations() -> list[LocationSummary]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    location_id,
                    location_type,
                    display_name,
                    accessibility_status,
                    COALESCE(confidence, 'unknown') AS confidence,
                    ST_Y(geom::geometry) AS lat,
                    ST_X(geom::geometry) AS lon
                FROM searchable_locations
                WHERE location_type = 'rail_station'
                ORDER BY
                    CASE
                        WHEN display_name ILIKE '%KL Sentral%' THEN 0
                        WHEN display_name ILIKE '%Pasar Seni%' THEN 1
                        WHEN display_name ILIKE '%Bukit Bintang%' THEN 2
                        ELSE 3
                    END,
                    display_name
                LIMIT 24
                """
            ).fetchall()
            # Query more rows first, then dedupe to keep enough meaningful results.
            deduped_rows = _dedupe_location_rows(rows, limit=8)
            return [_location_summary(row) for row in deduped_rows]
    except Exception as exc:
        logger.exception("Failed to load /locations/popular from database.")
        raise HTTPException(
            status_code=503,
            detail="Location data is temporarily unavailable.",
        ) from exc


@router.get("/search", response_model=list[LocationSummary])
def search_locations(q: str = "") -> list[LocationSummary]:
    query = q.strip()
    if not query:
        return []

    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    location_id,
                    location_type,
                    display_name,
                    accessibility_status,
                    COALESCE(confidence, 'unknown') AS confidence,
                    ST_Y(geom::geometry) AS lat,
                    ST_X(geom::geometry) AS lon
                FROM searchable_locations
                WHERE display_name ILIKE %(like_query)s
                ORDER BY similarity(display_name, %(query)s) DESC, display_name
                LIMIT 60
                """,
                {"query": query, "like_query": f"%{query}%"},
            ).fetchall()
            # Similarity ranking can still return name duplicates; normalize in API layer.
            deduped_rows = _dedupe_location_rows(rows, limit=20)
            return [_location_summary(row) for row in deduped_rows]
    except Exception as exc:
        logger.exception("Failed to load /locations/search from database.")
        raise HTTPException(
            status_code=503,
            detail="Location data is temporarily unavailable.",
        ) from exc


@router.get("/{location_id}", response_model=LocationDetail)
def location_detail(location_id: str) -> LocationDetail:
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    location_id,
                    location_type,
                    source_id,
                    display_name,
                    accessibility_status,
                    COALESCE(confidence, 'unknown') AS confidence,
                    ST_Y(geom::geometry) AS lat,
                    ST_X(geom::geometry) AS lon
                FROM searchable_locations
                WHERE location_id = %(location_id)s
                """,
                {"location_id": location_id},
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Location not found.")

            data = row
            routes: list[str] = []
            known_facilities: list[str] = []
            source_list = [data["source_id"]] if data.get("source_id") else []

            if data["location_type"] == "rail_station":
                member_rows = conn.execute(
                    """
                    SELECT station.station_id, station.source_system
                    FROM station_group_members member
                    JOIN rail_stations station ON station.station_id = member.station_id
                    WHERE member.station_group_id = %(station_group_id)s
                    ORDER BY station.source_system, station.station_name, station.station_id
                    """,
                    {"station_group_id": data["location_id"]},
                ).fetchall()
                station_ids = [member["station_id"] for member in member_rows]
                # Legacy rows may not have station_group_members yet.
                if not station_ids and data.get("source_id"):
                    station_ids = [data["source_id"]]

                # Aggregate route labels across all station members in the group.
                routes = [
                    route_row["route_name"]
                    for route_row in conn.execute(
                        """
                        SELECT route.route_short_name AS route_name
                        FROM rail_station_routes station_route
                        JOIN rail_routes route ON route.route_id = station_route.route_id
                        WHERE station_route.station_id = ANY(%(station_ids)s)
                          AND route.route_short_name IS NOT NULL
                        ORDER BY route.route_short_name
                        """,
                        {"station_ids": station_ids},
                    ).fetchall()
                    if route_row["route_name"]
                ]
                routes = sorted(set(routes))

                # Nearby accessibility facilities are inferred from points within
                # 50m of grouped station geometries.
                facility_row = conn.execute(
                    """
                    SELECT
                        BOOL_OR(LOWER(COALESCE(point.wheelchair, '')) IN ('yes', 'limited'))
                            AS wheelchair_access,
                        BOOL_OR(LOWER(COALESCE(point.shelter, '')) IN ('yes', 'limited'))
                            AS shelter,
                        BOOL_OR(LOWER(COALESCE(point.covered, '')) IN ('yes', 'limited'))
                            AS covered,
                        BOOL_OR(LOWER(COALESCE(point.tactile_paving, '')) IN ('yes', 'limited'))
                            AS tactile_paving,
                        BOOL_OR(LOWER(COALESCE(point.bench, '')) IN ('yes', 'limited'))
                            AS bench,
                        BOOL_OR(LOWER(COALESCE(point.kerb, '')) IN ('yes', 'limited'))
                            AS kerb
                    FROM rail_stations station
                    JOIN accessibility_points point
                      ON station.geom IS NOT NULL
                     AND point.geom IS NOT NULL
                     AND ST_DWithin(station.geom::geography, point.geom::geography, 50)
                    WHERE station.station_id = ANY(%(station_ids)s)
                    """,
                    {"station_ids": station_ids},
                ).fetchone()
                known_facilities = _supported_facilities(
                    facility_row or {},
                    data.get("accessibility_status") or "unknown",
                )

                source_list = sorted(
                    {
                        SOURCE_SYSTEM_LABELS.get(member["source_system"], member["source_system"])
                        for member in member_rows
                        if member.get("source_system")
                    },
                    key=lambda source: (SOURCE_SYSTEM_ORDER.get(source, 99), source),
                )
                note = _accessibility_note(data.get("accessibility_status") or "unknown")
            else:
                note = None

            return LocationDetail(
                id=data["location_id"],
                name=data["display_name"],
                type=data["location_type"],
                lat=data.get("lat"),
                lon=data.get("lon"),
                accessibility_status=data.get("accessibility_status") or "unknown",
                confidence=data.get("confidence") or "unknown",
                note=note,
                routes=routes,
                known_facilities=known_facilities,
                source_list=source_list,
            )
    except HTTPException:
        # Preserve explicit 404/other HTTP semantics but still try CSV fallback
        # for demo/local environments without fully populated DB views.
        csv_location = get_csv_location(location_id)
        if csv_location:
            return csv_location
        raise
    except Exception as exc:
        # Last-resort fallback for DB outages or missing views in local setups.
        csv_location = get_csv_location(location_id)
        if csv_location:
            return csv_location
        raise HTTPException(status_code=404, detail="Location not found.") from exc
