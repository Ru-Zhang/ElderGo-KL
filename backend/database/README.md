# ElderGo KL Data Plan Database

This folder implements the PostgreSQL/PostGIS database described in `DATA_PLAN.md`.
The schema intentionally uses the Data Plan table names, such as `rail_stations`,
`accessibility_points`, and `station_accessibility_profiles`.

## Files

- `schema.sql` creates the Data Plan tables, PostGIS/trigram extensions, and indexes.
- `import_to_postgres.py` imports the current `csv_output` files into the Data Plan schema.

## Source Of Truth

- The only schema initialization source is `backend/database/schema.sql`.
- The ETL entrypoint is `backend/database/import_to_postgres.py`.
- Do not maintain a parallel schema file under another path for deployment initialization.

## Requirements

- PostgreSQL with PostGIS support.
- Python 3.10+.
- Python dependency:

```powershell
pip install "psycopg[binary]"
```

## Local PostgreSQL Setup

Create a local test database:

```powershell
createdb -U postgres test
```

Enable required extensions:

```powershell
psql -U postgres -d test
```

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SELECT postgis_full_version();
\q
```

Set the database URL:

```powershell
$env:ELDERGO_DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/test"
```

## Import Data

From the project root:

```powershell
python database\import_to_postgres.py --reset
```

`--reset` drops the Data Plan tables and any older `transit_*` implementation tables
before recreating and importing data.

Use a different CSV folder if needed:

```powershell
python database\import_to_postgres.py --reset --csv-root D:\Monash_FIT\FIT5120\data_cleaning\csv_output
```

## Imported Data Flow

1. KTMB and Rapid Rail `agency.csv` files are imported into `rail_agencies`.
2. `routes.csv` files are imported into `rail_routes`.
3. `stops.csv` files are imported into `rail_stations`.
4. `trips.csv` and `stop_times.csv` are used to derive `rail_station_routes`.
5. `accessibility_feature_clean.csv` rows with `geom_type = Point` are imported into `accessibility_points`.
6. PostGIS 50m matching generates `station_accessibility_profiles`.
7. `rail_stations` and `accessibility_points` are synced into `searchable_locations`.

IDs are prefixed by source, for example:

```text
ktmb:50500
rapid_rail:KJ15
osm:node/1707840846
```

Missing accessibility data is stored as `unknown`, not `not_supported`.

## Verify Import

List tables:

```powershell
psql -U postgres -d test -c "\dt"
```

Check core row counts:

```sql
SELECT 'rail_agencies' AS table_name, COUNT(*) FROM rail_agencies
UNION ALL
SELECT 'rail_routes', COUNT(*) FROM rail_routes
UNION ALL
SELECT 'rail_stations', COUNT(*) FROM rail_stations
UNION ALL
SELECT 'rail_station_routes', COUNT(*) FROM rail_station_routes
UNION ALL
SELECT 'accessibility_points', COUNT(*) FROM accessibility_points
UNION ALL
SELECT 'station_accessibility_profiles', COUNT(*) FROM station_accessibility_profiles
UNION ALL
SELECT 'searchable_locations', COUNT(*) FROM searchable_locations;
```

Search Epic 6 locations:

```sql
SELECT location_id, location_type, display_name, accessibility_status, confidence
FROM searchable_locations
WHERE display_name ILIKE '%KL Sentral%'
ORDER BY similarity(display_name, 'KL Sentral') DESC
LIMIT 20;
```

Verify only Point accessibility geometry was imported:

```sql
SELECT DISTINCT ST_GeometryType(geom)
FROM accessibility_points
WHERE geom IS NOT NULL;
```

Find accessibility points within 50m of a station:

```sql
SELECT
    station.station_id,
    station.station_name,
    point.accessibility_point_id,
    point.name,
    ST_Distance(station.geom::geography, point.geom::geography) AS distance_m
FROM rail_stations station
JOIN accessibility_points point
  ON ST_DWithin(station.geom::geography, point.geom::geography, 50)
WHERE station.station_name ILIKE '%KL Sentral%'
ORDER BY distance_m
LIMIT 20;
```

Find the nearest rail station to a Google transit coordinate:

```sql
SELECT station_id, station_name
FROM rail_stations
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(101.6869, 3.1340), 4326)::geography,
    100
)
ORDER BY ST_Distance(
    geom::geography,
    ST_SetSRID(ST_MakePoint(101.6869, 3.1340), 4326)::geography
)
LIMIT 1;
```
