from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import psycopg
except ImportError as exc:  # pragma: no cover - user environment check
    raise SystemExit(
        "Missing dependency: psycopg. Install it with `pip install psycopg[binary]`."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_ROOT = ROOT / "csv_output"
SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")


@dataclass(frozen=True)
class GtfsSource:
    source_system: str
    folder_name: str
    default_operator: str


GTFS_SOURCES = [
    GtfsSource("ktmb", "ktmb_data", "KTMB"),
    GtfsSource("rapid_rail", "rapid_rail_data", "Rapid KL"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as src:
        return list(csv.DictReader(src))


def clean(value: Any) -> Any:
    if value is None:
        return None
    value = str(value).strip()
    return value if value != "" else None


def parse_bool(value: Any) -> bool | None:
    value = clean(value)
    if value is None:
        return None
    lowered = str(value).lower()
    if lowered in {"true", "t", "yes", "y", "1"}:
        return True
    if lowered in {"false", "f", "no", "n", "0"}:
        return False
    return None


def parse_int(value: Any) -> int | None:
    value = clean(value)
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def parse_float(value: Any) -> float | None:
    value = clean(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def prefixed(source_system: str, raw_id: Any) -> str | None:
    raw_id = clean(raw_id)
    if raw_id is None:
        return None
    return f"{source_system}:{raw_id}"


def osm_prefixed(source_id: Any) -> str | None:
    source_id = clean(source_id)
    if source_id is None:
        return None
    return f"osm:{source_id}"


def infer_rail_type(source_system: str, row: dict[str, str]) -> str:
    if source_system == "ktmb":
        return "KTM"

    category = clean(row.get("category"))
    if category:
        return category

    text = " ".join(
        str(clean(row.get(key)) or "")
        for key in ("route_short_name", "route_long_name", "route_desc")
    ).lower()
    if "mrt" in text:
        return "MRT"
    if "monorail" in text:
        return "Monorail"
    if "lrt" in text:
        return "LRT"
    return "unknown"


def jsonb_text(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return "null"
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            return json.dumps({"raw": value}, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def execute_schema(conn: psycopg.Connection[Any]) -> None:
    with SCHEMA_PATH.open("r", encoding="utf-8") as src:
        conn.execute(src.read())


def upsert_many(
    conn: psycopg.Connection[Any],
    sql: str,
    rows: Iterable[tuple[Any, ...]],
) -> int:
    count = 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(sql, row)
            count += 1
    return count


def fetch_key_set(conn: psycopg.Connection[Any], table_name: str, column_name: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT {column_name} FROM {table_name}")
        return {row[0] for row in cur.fetchall()}


def import_agencies(conn: psycopg.Connection[Any], csv_root: Path, source: GtfsSource) -> int:
    rows = read_csv(csv_root / source.folder_name / "agency.csv")

    def values() -> Iterable[tuple[Any, ...]]:
        for row in rows:
            agency_id = prefixed(source.source_system, row.get("agency_id"))
            if agency_id is None:
                continue
            yield (
                agency_id,
                source.source_system,
                clean(row.get("agency_name")) or source.default_operator,
                clean(row.get("agency_url")),
                clean(row.get("agency_timezone")),
            )

    return upsert_many(
        conn,
        """
        INSERT INTO rail_agencies (
            agency_id, source_system, agency_name, agency_url, agency_timezone
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (agency_id) DO UPDATE SET
            source_system = EXCLUDED.source_system,
            agency_name = EXCLUDED.agency_name,
            agency_url = EXCLUDED.agency_url,
            agency_timezone = EXCLUDED.agency_timezone
        """,
        values(),
    )


def import_routes(conn: psycopg.Connection[Any], csv_root: Path, source: GtfsSource) -> int:
    rows = read_csv(csv_root / source.folder_name / "routes.csv")

    def values() -> Iterable[tuple[Any, ...]]:
        for row in rows:
            route_id = prefixed(source.source_system, row.get("route_id"))
            if route_id is None:
                continue
            yield (
                route_id,
                prefixed(source.source_system, row.get("agency_id")),
                source.source_system,
                clean(row.get("route_short_name")),
                clean(row.get("route_long_name")),
                infer_rail_type(source.source_system, row),
                clean(row.get("route_color")),
            )

    return upsert_many(
        conn,
        """
        INSERT INTO rail_routes (
            route_id, agency_id, source_system, route_short_name,
            route_long_name, rail_type, route_color
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (route_id) DO UPDATE SET
            agency_id = EXCLUDED.agency_id,
            source_system = EXCLUDED.source_system,
            route_short_name = EXCLUDED.route_short_name,
            route_long_name = EXCLUDED.route_long_name,
            rail_type = EXCLUDED.rail_type,
            route_color = EXCLUDED.route_color
        """,
        values(),
    )


def import_stations(conn: psycopg.Connection[Any], csv_root: Path, source: GtfsSource) -> int:
    rows = read_csv(csv_root / source.folder_name / "stops.csv")

    def values() -> Iterable[tuple[Any, ...]]:
        for row in rows:
            station_id = prefixed(source.source_system, row.get("stop_id"))
            station_name = clean(row.get("stop_name"))
            lat = parse_float(row.get("stop_lat"))
            lon = parse_float(row.get("stop_lon"))
            if station_id is None or station_name is None:
                continue
            yield (
                station_id,
                source.source_system,
                clean(row.get("stop_id")),
                station_name,
                lat,
                lon,
                lon,
                lat,
            )

    return upsert_many(
        conn,
        """
        INSERT INTO rail_stations (
            station_id, source_system, stop_id, station_name, lat, lon, geom
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            CASE
                WHEN %s IS NULL OR %s IS NULL THEN NULL
                ELSE ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            END
        )
        ON CONFLICT (station_id) DO UPDATE SET
            source_system = EXCLUDED.source_system,
            stop_id = EXCLUDED.stop_id,
            station_name = EXCLUDED.station_name,
            lat = EXCLUDED.lat,
            lon = EXCLUDED.lon,
            geom = EXCLUDED.geom
        """,
        ((a, b, c, d, e, f, g, h, g, h) for a, b, c, d, e, f, g, h in values()),
    )


def trip_route_map(csv_root: Path, source: GtfsSource) -> dict[str, tuple[str, str | None]]:
    rows = read_csv(csv_root / source.folder_name / "trips.csv")
    mapping: dict[str, tuple[str, str | None]] = {}
    for row in rows:
        trip_id = clean(row.get("trip_id"))
        route_id = prefixed(source.source_system, row.get("route_id"))
        if trip_id is None or route_id is None:
            continue
        mapping[trip_id] = (route_id, clean(row.get("direction_id")))
    return mapping


def import_station_routes(conn: psycopg.Connection[Any], csv_root: Path, source: GtfsSource) -> int:
    rows = read_csv(csv_root / source.folder_name / "stop_times.csv")
    trip_routes = trip_route_map(csv_root, source)
    existing_routes = fetch_key_set(conn, "rail_routes", "route_id")
    existing_stations = fetch_key_set(conn, "rail_stations", "station_id")
    seen: set[tuple[str, str, int | None, str | None]] = set()

    def values() -> Iterable[tuple[Any, ...]]:
        for row in rows:
            trip_id = clean(row.get("trip_id"))
            route_id: str | None = None
            direction_id: str | None = None

            if trip_id in trip_routes:
                route_id, direction_id = trip_routes[trip_id]
            elif clean(row.get("route_id")) is not None:
                route_id = prefixed(source.source_system, row.get("route_id"))
                direction_id = clean(row.get("direction_id"))

            station_id = prefixed(source.source_system, row.get("stop_id"))
            stop_sequence = parse_int(row.get("stop_sequence"))
            if route_id is None or station_id is None:
                continue
            if route_id not in existing_routes or station_id not in existing_stations:
                continue

            key = (station_id, route_id, stop_sequence, direction_id)
            if key in seen:
                continue
            seen.add(key)
            sequence_text = "none" if stop_sequence is None else str(stop_sequence)
            direction_text = "none" if direction_id is None else direction_id
            station_route_id = f"{route_id}:{direction_text}:{sequence_text}:{station_id}"
            yield (station_route_id, station_id, route_id, stop_sequence, direction_id)

    return upsert_many(
        conn,
        """
        INSERT INTO rail_station_routes (
            station_route_id, station_id, route_id, stop_sequence, direction_id
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (station_route_id) DO UPDATE SET
            station_id = EXCLUDED.station_id,
            route_id = EXCLUDED.route_id,
            stop_sequence = EXCLUDED.stop_sequence,
            direction_id = EXCLUDED.direction_id
        """,
        values(),
    )


def display_name(row: dict[str, str]) -> str | None:
    return (
        clean(row.get("name_en"))
        or clean(row.get("name_ms"))
        or clean(row.get("name_default"))
        or clean(row.get("accessibility_type"))
        or clean(row.get("source_id"))
    )


def import_accessibility_points(conn: psycopg.Connection[Any], csv_root: Path) -> int:
    rows = read_csv(csv_root / "accessibility_feature_clean.csv")

    def values() -> Iterable[tuple[Any, ...]]:
        for row in rows:
            if str(clean(row.get("geom_type")) or "").lower() != "point":
                continue
            point_id = osm_prefixed(row.get("source_id"))
            geom_wkt = clean(row.get("geom_wkt"))
            if point_id is None or geom_wkt is None:
                continue
            yield (
                point_id,
                clean(row.get("source_id")),
                display_name(row),
                clean(row.get("name_en")),
                clean(row.get("name_ms")),
                clean(row.get("feature_type")),
                clean(row.get("accessibility_type")),
                clean(row.get("wheelchair")),
                clean(row.get("shelter")),
                clean(row.get("covered")),
                clean(row.get("tactile_paving")),
                clean(row.get("kerb")),
                clean(row.get("bench")),
                geom_wkt,
                jsonb_text(row.get("raw_properties")),
            )

    return upsert_many(
        conn,
        """
        INSERT INTO accessibility_points (
            accessibility_point_id, source_id, name, name_en, name_ms,
            feature_type, accessibility_type, wheelchair, shelter, covered,
            tactile_paving, kerb, bench, geom, raw_properties
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            ST_GeomFromText(%s, 4326),
            %s::jsonb
        )
        ON CONFLICT (accessibility_point_id) DO UPDATE SET
            source_id = EXCLUDED.source_id,
            name = EXCLUDED.name,
            name_en = EXCLUDED.name_en,
            name_ms = EXCLUDED.name_ms,
            feature_type = EXCLUDED.feature_type,
            accessibility_type = EXCLUDED.accessibility_type,
            wheelchair = EXCLUDED.wheelchair,
            shelter = EXCLUDED.shelter,
            covered = EXCLUDED.covered,
            tactile_paving = EXCLUDED.tactile_paving,
            kerb = EXCLUDED.kerb,
            bench = EXCLUDED.bench,
            geom = EXCLUDED.geom,
            raw_properties = EXCLUDED.raw_properties
        """,
        values(),
    )


def rapid_oku_station_ids(csv_root: Path) -> list[str]:
    source = GtfsSource("rapid_rail", "rapid_rail_data", "Rapid KL")
    rows = read_csv(csv_root / source.folder_name / "stops.csv")
    station_ids: list[str] = []
    for row in rows:
        if parse_bool(row.get("isOKU")) is True:
            station_id = prefixed(source.source_system, row.get("stop_id"))
            if station_id is not None:
                station_ids.append(station_id)
    return station_ids


def refresh_station_accessibility_profiles(
    conn: psycopg.Connection[Any], csv_root: Path
) -> None:
    conn.execute("CREATE TEMP TABLE tmp_rapid_oku_stations (station_id TEXT PRIMARY KEY) ON COMMIT DROP")
    upsert_many(
        conn,
        "INSERT INTO tmp_rapid_oku_stations (station_id) VALUES (%s) ON CONFLICT DO NOTHING",
        ((station_id,) for station_id in rapid_oku_station_ids(csv_root)),
    )

    conn.execute(
        """
        INSERT INTO station_accessibility_profiles (
            station_id, accessibility_status, confidence, source_list, note
        )
        SELECT
            station.station_id,
            CASE
                WHEN oku.station_id IS NOT NULL THEN 'supported'
                WHEN EXISTS (
                    SELECT 1
                    FROM accessibility_points point
                    WHERE LOWER(COALESCE(point.wheelchair, '')) = 'yes'
                      AND station.geom IS NOT NULL
                      AND point.geom IS NOT NULL
                      AND ST_DWithin(station.geom::geography, point.geom::geography, 50)
                ) THEN 'supported'
                ELSE 'unknown'
            END,
            CASE
                WHEN oku.station_id IS NOT NULL THEN 'high'
                WHEN EXISTS (
                    SELECT 1
                    FROM accessibility_points point
                    WHERE LOWER(COALESCE(point.wheelchair, '')) = 'yes'
                      AND station.geom IS NOT NULL
                      AND point.geom IS NOT NULL
                      AND ST_DWithin(station.geom::geography, point.geom::geography, 50)
                ) THEN 'medium'
                ELSE 'low'
            END,
            CASE
                WHEN oku.station_id IS NOT NULL THEN '["rapid_rail_isOKU"]'::jsonb
                WHEN EXISTS (
                    SELECT 1
                    FROM accessibility_points point
                    WHERE LOWER(COALESCE(point.wheelchair, '')) = 'yes'
                      AND station.geom IS NOT NULL
                      AND point.geom IS NOT NULL
                      AND ST_DWithin(station.geom::geography, point.geom::geography, 50)
                ) THEN '["accessibility_point_50m"]'::jsonb
                ELSE '[]'::jsonb
            END,
            CASE
                WHEN oku.station_id IS NOT NULL THEN 'Rapid Rail isOKU=true.'
                WHEN EXISTS (
                    SELECT 1
                    FROM accessibility_points point
                    WHERE LOWER(COALESCE(point.wheelchair, '')) = 'yes'
                      AND station.geom IS NOT NULL
                      AND point.geom IS NOT NULL
                      AND ST_DWithin(station.geom::geography, point.geom::geography, 50)
                ) THEN 'Wheelchair accessibility point found within 50 metres.'
                ELSE 'No static accessibility support data found.'
            END
        FROM rail_stations station
        LEFT JOIN tmp_rapid_oku_stations oku ON oku.station_id = station.station_id
        ON CONFLICT (station_id) DO UPDATE SET
            accessibility_status = EXCLUDED.accessibility_status,
            confidence = EXCLUDED.confidence,
            source_list = EXCLUDED.source_list,
            note = EXCLUDED.note
        """
    )


def refresh_searchable_locations(conn: psycopg.Connection[Any]) -> None:
    conn.execute("DELETE FROM searchable_locations")
    conn.execute(
        """
        INSERT INTO searchable_locations (
            location_id, location_type, source_id, display_name,
            geom, accessibility_status, confidence
        )
        SELECT
            station.station_id,
            'rail_station',
            station.stop_id,
            station.station_name,
            station.geom,
            COALESCE(profile.accessibility_status, 'unknown'),
            COALESCE(profile.confidence, 'low')
        FROM rail_stations station
        LEFT JOIN station_accessibility_profiles profile
            ON profile.station_id = station.station_id
        """
    )
    conn.execute(
        """
        INSERT INTO searchable_locations (
            location_id, location_type, source_id, display_name,
            geom, accessibility_status, confidence
        )
        SELECT
            point.accessibility_point_id,
            COALESCE(point.feature_type, 'accessibility_point'),
            point.source_id,
            COALESCE(point.name, point.name_en, point.name_ms, point.source_id, point.accessibility_point_id),
            point.geom,
            CASE WHEN LOWER(COALESCE(point.wheelchair, '')) = 'yes' THEN 'supported' ELSE 'unknown' END,
            CASE WHEN LOWER(COALESCE(point.wheelchair, '')) = 'yes' THEN 'medium' ELSE 'low' END
        FROM accessibility_points point
        WHERE point.geom IS NOT NULL
        """
    )


def import_gtfs_source(
    conn: psycopg.Connection[Any], csv_root: Path, source: GtfsSource
) -> dict[str, int]:
    return {
        f"{source.source_system}_rail_agencies": import_agencies(conn, csv_root, source),
        f"{source.source_system}_rail_routes": import_routes(conn, csv_root, source),
        f"{source.source_system}_rail_stations": import_stations(conn, csv_root, source),
        f"{source.source_system}_rail_station_routes": import_station_routes(conn, csv_root, source),
    }


def reset_tables(conn: psycopg.Connection[Any]) -> None:
    conn.execute(
        """
        DROP TABLE IF EXISTS
            ai_messages,
            ai_conversations,
            searchable_locations,
            route_accessibility_annotations,
            route_steps,
            recommended_routes,
            route_requests,
            recent_place_cache,
            user_travel_preferences,
            user_ui_settings,
            anonymous_users,
            station_accessibility_profiles,
            accessibility_points,
            rail_station_routes,
            rail_stations,
            rail_routes,
            rail_agencies,
            location_services,
            search_aliases,
            shared_route_links,
            saved_routes,
            stop_accessibility_profiles,
            transit_accessibility_points,
            accessibility_features,
            transit_shapes,
            transit_frequencies,
            transit_stop_times,
            transit_trips,
            transit_calendar,
            transit_stops,
            transit_routes,
            transit_agencies
        CASCADE
        """
    )


def import_all(connection_string: str, csv_root: Path, reset: bool) -> dict[str, int]:
    stats: dict[str, int] = {}
    with psycopg.connect(connection_string) as conn:
        if reset:
            reset_tables(conn)

        execute_schema(conn)

        for source in GTFS_SOURCES:
            stats.update(import_gtfs_source(conn, csv_root, source))

        stats["accessibility_points"] = import_accessibility_points(conn, csv_root)
        refresh_station_accessibility_profiles(conn, csv_root)
        refresh_searchable_locations(conn)
        stats["station_accessibility_profiles"] = len(
            fetch_key_set(conn, "station_accessibility_profiles", "station_id")
        )
        stats["searchable_locations"] = len(fetch_key_set(conn, "searchable_locations", "location_id"))

        conn.commit()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the ElderGo KL Data Plan schema and import current CSV outputs."
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--csv-root",
        default=str(DEFAULT_CSV_ROOT),
        help="Path to csv_output directory.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop ElderGo Data Plan tables before recreating and importing data.",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Provide --database-url or set DATABASE_URL.")

    stats = import_all(args.database_url, Path(args.csv_root), args.reset)
    print("Import complete.")
    for key in sorted(stats):
        print(f"{key}: {stats[key]}")


if __name__ == "__main__":
    main()
