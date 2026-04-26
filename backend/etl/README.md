# ElderGo KL ETL

This folder contains the DATA_PLAN ETL importer copied from `data.zip`.

1. Import KTMB GTFS CSV.
2. Import Rapid Rail GTFS CSV.
3. Import cleaned accessibility Point CSV.
4. Build station accessibility profiles.
5. Sync `searchable_locations`.

Bus route data is intentionally not imported in the current stage. Bus routing comes from Google Maps.

## Run Locally

From the repo root:

```powershell
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/eldergo_kl"
python backend\etl\import_to_postgres.py --reset
```

The importer reads CSV files from:

```text
data/csv_output
```
