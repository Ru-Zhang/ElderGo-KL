import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.paths import CSV_OUTPUT_DIR, MRT_FACILITIES_CSV, ROUTE_STATION_IMAGES_CSV
from app.services.gemini_client import GEMINI_KEY_POOL

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def log_startup_data_and_ai_config() -> None:
    if not MRT_FACILITIES_CSV.is_file():
        logger.warning("Bundled data missing: %s", MRT_FACILITIES_CSV)
    if not ROUTE_STATION_IMAGES_CSV.is_file():
        logger.warning("Bundled data missing: %s", ROUTE_STATION_IMAGES_CSV)
    if not CSV_OUTPUT_DIR.is_dir():
        logger.warning("CSV fallback directory missing: %s", CSV_OUTPUT_DIR)
    if not GEMINI_KEY_POOL.has_configured_keys():
        logger.warning(
            "No Gemini API keys configured — chatbot will use DB/flow fallbacks only. "
            "Set ELDERGO_GEMINI_API_KEY_PRIMARY (and optional SECONDARY / ELDERGO_GEMINI_API_KEYS)."
        )
    else:
        logger.info("Gemini key pool ready (%d key(s))", len(GEMINI_KEY_POOL.collect_unique_keys()))

# CORS stays open to configured frontend origins so local web and deployed UI
# can call the API without browser preflight failures.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount at root (local + Render) and under /api/v1 (Render health check + docs).
app.include_router(api_router)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    # Simple root endpoint used as quick service sanity check.
    return {"name": settings.app_name, "status": "ok"}
