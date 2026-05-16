from typing import Literal

from pydantic import BaseModel, Field


DepartureTime = Literal[
    "now",
    "morning_peak",
    "midday",
    "evening_peak",
    "night",
    "morning",
    "afternoon",
    "evening",
]
WeatherRiskLevel = Literal["clear", "rain", "hot", "storm", "unavailable"]


class WeatherForecastRequest(BaseModel):
    # Destination name is mandatory so backend can geocode when lat/lon are absent.
    destination_name: str = Field(min_length=1)
    lat: float | None = None
    lon: float | None = None
    departure_time: str = "now"


class WeatherHourlySlot(BaseModel):
    forecast_time: str
    temperature_c: float
    feels_like_c: float
    weather_description: str
    precipitation_probability_percent: int | None = None
    is_departure_window: bool = False


class WeatherForecastResponse(BaseModel):
    destination_name: str
    forecast_time: str
    period_label: str
    departure_forecast_label: str | None = None
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
    rain_period_start: str | None = None
    rain_period_end: str | None = None
    rain_window_hours: int | None = None
    peak_pop_percent: int | None = None
    hourly_outlook: list[WeatherHourlySlot] = Field(default_factory=list)
