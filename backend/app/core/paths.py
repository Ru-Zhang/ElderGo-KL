"""Stable filesystem paths for bundled CSV/JSON data (local dev and Render).

Paths are resolved from this file's location, not from process cwd, so
`gunicorn --chdir backend` and `uvicorn` from the repo root behave the same.
"""

from pathlib import Path

# backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
CSV_OUTPUT_DIR = BACKEND_DIR / "csv_output"

MRT_FACILITIES_CSV = DATA_DIR / "mrt_stations_facilities.csv"
ROUTE_STATION_IMAGES_CSV = DATA_DIR / "route_station_images.csv"
ROUTE_STATION_IMAGES_LINKED_CSV = DATA_DIR / "route_station_images_linked.csv"
ROUTE_SEGMENT_IMAGE_TEMPLATES_CSV = DATA_DIR / "route_segment_image_templates.csv"
RIDERSHIP_CSV = DATA_DIR / "rapidkl_ridership_2024_2026_final_predicted_july_2026.csv"
