# ElderGo KL ETL

This folder is reserved for the DATA_PLAN ETL workflow:

1. Import KTMB GTFS CSV.
2. Import Rapid Rail GTFS CSV.
3. Import cleaned accessibility Point CSV.
4. Build station accessibility profiles.
5. Sync `searchable_locations`.

Bus route data is intentionally not imported in the current stage. Bus routing comes from Google Maps.
