import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "ElderGo KL API"
    environment: str = Field(default="development", alias="ELDERGO_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://eldergo:eldergo@localhost:5432/eldergo_kl",
        alias="ELDERGO_DATABASE_URL",
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ELDERGO_CORS_ORIGINS",
    )
    google_maps_api_key: str = Field(default="", alias="ELDERGO_GOOGLE_MAPS_API_KEY")
    openweather_api_key: str = Field(default="", alias="OPENWEATHER_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="ELDERGO_GEMINI_MODEL")
    gemini_api_key_primary: str = Field(default="", alias="ELDERGO_GEMINI_API_KEY_PRIMARY")
    gemini_api_key_secondary: str = Field(default="", alias="ELDERGO_GEMINI_API_KEY_SECONDARY")
    gemini_api_keys: str = Field(default="", alias="ELDERGO_GEMINI_API_KEYS")
    gemini_intent_routing_enabled: bool = Field(
        default=True, alias="ELDERGO_GEMINI_INTENT_ROUTING_ENABLED"
    )
    ai_guardrail_enabled: bool = Field(default=True, alias="ELDERGO_AI_GUARDRAIL_ENABLED")
    ai_guardrail_mode: str = Field(default="hybrid", alias="ELDERGO_AI_GUARDRAIL_MODE")
    ai_guardrail_strict: bool = Field(default=False, alias="ELDERGO_AI_GUARDRAIL_STRICT")
    demo_mode: bool = Field(default=True, alias="ELDERGO_DEMO_MODE")
    # Off by default so route planning does not hold DB connections after the response.
    persist_route_snapshots: bool = Field(default=False, alias="ELDERGO_PERSIST_ROUTE_SNAPSHOTS")
    route_cache_ttl_seconds: int = Field(default=900, alias="ELDERGO_ROUTE_CACHE_TTL_SECONDS")
    route_cache_max_entries: int = Field(default=64, alias="ELDERGO_ROUTE_CACHE_MAX_ENTRIES")

    model_config = SettingsConfigDict(
        env_file=(
            ROOT_DIR / ".env",
            BACKEND_DIR / ".env",
        ),
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        # Keep env var format simple (comma-separated string) while exposing a
        # normalized list to FastAPI CORS middleware.
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # Backward-compatibility bridge for legacy env name still used in some local
    # setups and deployment environments.
    if "GOOGLE_MAPS_API_KEY" in os.environ and "ELDERGO_GOOGLE_MAPS_API_KEY" not in os.environ:
        os.environ["ELDERGO_GOOGLE_MAPS_API_KEY"] = os.environ["GOOGLE_MAPS_API_KEY"]
    return Settings()
