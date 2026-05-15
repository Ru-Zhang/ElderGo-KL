"""Shared location search/detail helpers for chatbot flows and API."""

import logging
import re

from fastapi import HTTPException

from app.schemas.locations import LocationDetail, LocationSummary
from app.services.database import get_connection
from app.services.mrt_facilities_service import get_mrt_facilities

logger = logging.getLogger(__name__)

SOURCE_SYSTEM_LABELS = {
    "rapid_rail": "Rapid Rail",
    "ktmb": "KTMB",
}
SOURCE_SYSTEM_ORDER = {
    "Rapid Rail": 0,
    "KTMB": 1,
}


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


def _canonical_station_name(value: str) -> str:
    normalized = re.sub(r"\s*[-–—]?\s*REDONE$", "", value.strip(), flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"(?<=[A-Z])\s+(?=\d)", "", normalized.upper())
    return normalized.upper()


def _dedupe_location_rows(rows: list[dict], limit: int) -> list[dict]:
    deduped: list[dict] = []
    seen_ids: set[str] = set()
    seen_station_names: set[str] = set()
    seen_display_names: set[str] = set()

    for row in rows:
        location_id = str(row["location_id"])
        if location_id in seen_ids:
            continue
        seen_ids.add(location_id)

        display_key = re.sub(r"\s+", " ", row["display_name"].strip().lower())
        if display_key in seen_display_names:
            continue
        seen_display_names.add(display_key)

        if row.get("location_type") == "rail_station":
            canonical_name = _canonical_station_name(row["display_name"])
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
        routes=list(row.get("routes") or []),
    )


def search_station_locations(query: str, limit: int = 20) -> list[LocationSummary]:
    cleaned = query.strip()
    if not cleaned:
        return []

    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    sl.location_id,
                    sl.location_type,
                    sl.display_name,
                    sl.accessibility_status,
                    COALESCE(sl.confidence, 'unknown') AS confidence,
                    ST_Y(sl.geom::geometry) AS lat,
                    ST_X(sl.geom::geometry) AS lon,
                    COALESCE(ARRAY(
                        SELECT DISTINCT route.route_short_name
                        FROM station_group_members member
                        JOIN rail_station_routes station_route
                          ON station_route.station_id = member.station_id
                        JOIN rail_routes route
                          ON route.route_id = station_route.route_id
                        WHERE member.station_group_id = sl.location_id
                          AND route.route_short_name IS NOT NULL
                        ORDER BY route.route_short_name
                    ), ARRAY[]::TEXT[]) AS routes
                FROM searchable_locations sl
                WHERE sl.location_type = 'rail_station'
                  AND sl.display_name ILIKE %(like_query)s
                ORDER BY similarity(sl.display_name, %(query)s) DESC, sl.display_name
                LIMIT 60
                """,
                {"query": cleaned, "like_query": f"%{cleaned}%"},
            ).fetchall()
            deduped_rows = _dedupe_location_rows(rows, limit=limit)
            return [_location_summary(row) for row in deduped_rows]
    except Exception as exc:
        logger.exception("Failed to search station locations.")
        raise HTTPException(
            status_code=503,
            detail="Location data is temporarily unavailable.",
        ) from exc


def get_location_detail_by_id(location_id: str) -> LocationDetail | None:
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
                return None

            data = row
            routes: list[str] = []
            known_facilities: list[str] = []
            source_list = [data["source_id"]] if data.get("source_id") else []
            station_facilities: list[str] = []
            station_address: str | None = None
            station_hours_summary: str | None = None
            facility_source_url: str | None = None

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
                if not station_ids and data.get("source_id"):
                    station_ids = [data["source_id"]]

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

                mrt = get_mrt_facilities(data["location_id"]) or {}
                station_facilities = mrt.get("station_facilities") or []
                station_address = mrt.get("station_address")
                station_hours_summary = mrt.get("station_hours_summary")
                facility_source_url = mrt.get("facility_source_url")

            summary = _location_summary(
                {
                    "location_id": data["location_id"],
                    "location_type": data["location_type"],
                    "display_name": data["display_name"],
                    "accessibility_status": data["accessibility_status"],
                    "confidence": data["confidence"],
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "routes": routes,
                }
            )
            return LocationDetail(
                **summary.model_dump(),
                known_facilities=known_facilities,
                source_list=source_list,
                station_facilities=station_facilities,
                station_address=station_address,
                station_hours_summary=station_hours_summary,
                facility_source_url=facility_source_url,
            )
    except Exception as exc:
        logger.exception("Failed to load location detail for %s", location_id)
        raise HTTPException(
            status_code=503,
            detail="Location data is temporarily unavailable.",
        ) from exc
