from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    demo_mode: bool = Field(default=True, alias="ELDERGO_DEMO_MODE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
