from typing import Literal

from pydantic import BaseModel, Field


DepartureTime = Literal["now", "morning", "afternoon", "evening"]
WeatherRiskLevel = Literal["clear", "rain", "hot", "storm", "unavailable"]


class WeatherForecastRequest(BaseModel):
    destination_name: str = Field(min_length=1)
    lat: float | None = None
    lon: float | None = None
    departure_time: DepartureTime = "now"


class WeatherForecastResponse(BaseModel):
    destination_name: str
    forecast_time: str
    period_label: DepartureTime
    temperature_c: float
    feels_like_c: float
    humidity_percent: int | None = None
    rain_mm: float = 0
    precipitation_probability_percent: int | None = None
    wind_kmh: float
    weather_main: str
    weather_description: str
    weather_icon: str | None = None
    risk_level: WeatherRiskLevel
    senior_advice: list[str]
