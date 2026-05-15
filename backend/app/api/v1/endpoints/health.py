import csv

from fastapi import APIRouter, HTTPException

from app.core.paths import (
    CSV_OUTPUT_DIR,
    MRT_FACILITIES_CSV,
    ROUTE_STATION_IMAGES_CSV,
)
from app.services.database import get_connection
from app.services.gemini_client import GEMINI_KEY_POOL

router = APIRouter()


def _csv_status(path) -> dict:
    if not path.is_file():
        return {"status": "missing", "path": str(path)}
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            row_count = sum(1 for _ in csv.DictReader(handle))
    except OSError:
        row_count = None
    return {"status": "ok", "path": str(path), "row_count": row_count}


@router.get("/health")
def health() -> dict[str, str]:
    # Lightweight liveness probe (process is running).
    return {"status": "ok"}


@router.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        with get_connection() as conn:
            # Minimal round-trip query used by readiness checks.
            conn.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/health/data")
def health_data() -> dict:
    """Readiness check for bundled CSV assets and Gemini key configuration (no secrets)."""
    keys = GEMINI_KEY_POOL.collect_unique_keys()
    return {
        "status": "ok",
        "mrt_facilities_csv": _csv_status(MRT_FACILITIES_CSV),
        "route_station_images_csv": _csv_status(ROUTE_STATION_IMAGES_CSV),
        "csv_output_dir": {
            "status": "ok" if CSV_OUTPUT_DIR.is_dir() else "missing",
            "path": str(CSV_OUTPUT_DIR),
        },
        "gemini_keys_configured": len(keys),
        "gemini_pool_ready": GEMINI_KEY_POOL.has_configured_keys(),
    }
