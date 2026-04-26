from fastapi import APIRouter, HTTPException

from app.schemas.locations import LocationDetail, LocationSummary
from app.services.csv_locations_service import get_csv_location, popular_csv_locations, search_csv_locations
from app.services.database import get_connection

router = APIRouter()


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
                LIMIT 8
                """
            ).fetchall()
            return [_location_summary(row) for row in rows]
    except Exception as exc:
        return popular_csv_locations()


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
                LIMIT 20
                """,
                {"query": query, "like_query": f"%{query}%"},
            ).fetchall()
            return [_location_summary(row) for row in rows]
    except Exception as exc:
        return search_csv_locations(query)


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
                routes = [
                    route_row["route_name"]
                    for route_row in conn.execute(
                        """
                        SELECT COALESCE(route.route_short_name, route.route_long_name, route.rail_type) AS route_name
                        FROM rail_station_routes station_route
                        JOIN rail_routes route ON route.route_id = station_route.route_id
                        WHERE station_route.station_id = %(station_id)s
                        ORDER BY route.route_short_name NULLS LAST, route.route_long_name NULLS LAST
                        """,
                        {"station_id": data["source_id"]},
                    ).fetchall()
                    if route_row["route_name"]
                ]

                profile = conn.execute(
                    """
                    SELECT note, source_list
                    FROM station_accessibility_profiles
                    WHERE station_id = %(station_id)s
                    """,
                    {"station_id": data["source_id"]},
                ).fetchone()
                note = profile["note"] if profile else None
                if profile and profile["source_list"]:
                    source_list = list(profile["source_list"])
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
        csv_location = get_csv_location(location_id)
        if csv_location:
            return csv_location
        raise
    except Exception as exc:
        csv_location = get_csv_location(location_id)
        if csv_location:
            return csv_location
        raise HTTPException(status_code=404, detail="Location not found.") from exc
