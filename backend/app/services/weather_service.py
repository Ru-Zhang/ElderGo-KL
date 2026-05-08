from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.weather import DepartureTime, WeatherForecastRequest, WeatherForecastResponse, WeatherRiskLevel
from app.services.places_service import get_station_place_detail

OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
OPENWEATHER_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"


def _target_hour(departure_time: DepartureTime) -> int:
    return {
        "morning": 9,
        "afternoon": 14,
        "evening": 19,
    }.get(departure_time, datetime.now().hour)


def _select_forecast_item(items: list[dict[str, Any]], departure_time: DepartureTime, timezone_offset: int) -> dict[str, Any]:
    if not items:
        raise HTTPException(status_code=502, detail="OpenWeatherMap did not return forecast items.")
    if departure_time == "now":
        return items[0]

    # Forecast timestamps are UTC; convert using city offset so morning/afternoon/
    # evening choices align with destination local time.
    local_tz = timezone(timedelta(seconds=timezone_offset))
    now_local = datetime.now(local_tz)
    target_local = now_local.replace(hour=_target_hour(departure_time), minute=0, second=0, microsecond=0)
    if target_local <= now_local:
        target_local += timedelta(days=1)

    def distance_from_target(item: dict[str, Any]) -> float:
        forecast_local = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(local_tz)
        return abs((forecast_local - target_local).total_seconds())

    return min(items, key=distance_from_target)


async def _geocode_destination(destination_name: str, api_key: str) -> tuple[float, float]:
    base_name = destination_name.strip()
    queries = [base_name, f"{base_name}, Malaysia", f"{base_name}, Kuala Lumpur, Malaysia"]
    # For short local station-style codes like "USJ7", enrich context for geocoding.
    normalized = base_name.replace(" ", "")
    if normalized and normalized.isalnum() and len(normalized) <= 8:
        queries.extend(
            [
                f"{base_name} station, Malaysia",
                f"{base_name} LRT station, Subang Jaya, Malaysia",
                f"{base_name} MRT station, Selangor, Malaysia",
            ]
        )

    # Try increasingly specific query variants before failing geocoding.
    async with httpx.AsyncClient(timeout=10) as client:
        for query in queries:
            response = await client.get(
                OPENWEATHER_GEOCODING_URL,
                params={
                    "q": query,
                    "limit": 5,
                    "appid": api_key,
                },
            )
            response.raise_for_status()
            results = response.json()
            if not isinstance(results, list) or not results:
                continue
            malaysia_result = next((item for item in results if item.get("country") == "MY"), None)
            result = malaysia_result or results[0]
            lat = result.get("lat")
            lon = result.get("lon")
            if lat is not None and lon is not None:
                return float(lat), float(lon)

    raise HTTPException(status_code=404, detail="Unable to find destination coordinates for weather forecast.")


async def _google_places_fallback_coordinates(destination_name: str) -> tuple[float, float] | None:
    try:
        detail = await get_station_place_detail(destination_name)
    # Google fallback is best-effort and should not mask primary geocoding errors.
    except Exception:
        return None

    if detail.lat is None or detail.lon is None:
        return None

    return float(detail.lat), float(detail.lon)


def _risk_level(item: dict[str, Any], rain_mm: float, wind_kmh: float) -> WeatherRiskLevel:
    weather_id = int((item.get("weather") or [{}])[0].get("id") or 0)
    main = item.get("main") or {}
    feels_like = float(main.get("feels_like") or main.get("temp") or 0)
    if weather_id >= 200 and weather_id < 300:
        return "storm"
    if rain_mm > 0 or weather_id in {500, 501, 502, 503, 504, 511, 520, 521, 522, 531}:
        return "rain"
    if feels_like >= 34:
        return "hot"
    # Strong wind is treated as storm-level risk for elderly trip planning.
    if wind_kmh >= 35:
        return "storm"
    return "clear"


def _senior_advice(risk_level: WeatherRiskLevel) -> list[str]:
    if risk_level == "storm":
        return [
            "Consider delaying the trip if the weather worsens.",
            "Ask station staff for help and use lifts or covered paths where possible.",
        ]
    if risk_level == "rain":
        return [
            "Bring an umbrella or raincoat and use covered walkways where possible.",
            "Floors may be slippery, so hold handrails and allow extra walking time.",
        ]
    if risk_level == "hot":
        return [
            "Bring water and rest in shaded or air-conditioned areas when needed.",
            "Avoid rushing between platforms; take lifts or escalators if available.",
        ]
    return [
        "Use the recommended route and walk at a comfortable pace.",
        "Keep your phone charged and leave a little extra time for transfers.",
    ]


async def get_weather_forecast(payload: WeatherForecastRequest) -> WeatherForecastResponse:
    settings = get_settings()
    if not settings.openweather_api_key:
        raise HTTPException(status_code=503, detail="OpenWeatherMap API key is not configured.")

    lat = payload.lat
    lon = payload.lon
    # Respect provided coordinates first; only geocode when client has no location.
    if lat is None or lon is None:
        try:
            lat, lon = await _geocode_destination(payload.destination_name, settings.openweather_api_key)
        except HTTPException:
            # If OpenWeather geocoding misses local station names, retry via Places.
            fallback = await _google_places_fallback_coordinates(payload.destination_name)
            if not fallback:
                raise
            lat, lon = fallback

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                OPENWEATHER_FORECAST_URL,
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.openweather_api_key,
                    "units": "metric",
                },
            )
            response.raise_for_status()
            body = response.json()
    except Exception:
        raise

    items = body.get("list") or []
    city = body.get("city") or {}
    selected = _select_forecast_item(items, payload.departure_time, int(city.get("timezone") or 0))
    main = selected.get("main") or {}
    weather = (selected.get("weather") or [{}])[0]
    wind = selected.get("wind") or {}
    rain = selected.get("rain") or {}
    rain_mm = float(rain.get("3h") or 0)
    wind_kmh = round(float(wind.get("speed") or 0) * 3.6, 1)
    risk_level = _risk_level(selected, rain_mm, wind_kmh)

    return WeatherForecastResponse(
        destination_name=city.get("name") or payload.destination_name,
        forecast_time=selected.get("dt_txt") or datetime.fromtimestamp(selected["dt"], tz=timezone.utc).isoformat(),
        period_label=payload.departure_time,
        temperature_c=round(float(main.get("temp") or 0), 1),
        feels_like_c=round(float(main.get("feels_like") or main.get("temp") or 0), 1),
        humidity_percent=main.get("humidity"),
        rain_mm=rain_mm,
        precipitation_probability_percent=round(float(selected.get("pop") or 0) * 100),
        wind_kmh=wind_kmh,
        weather_main=weather.get("main") or "Weather",
        weather_description=weather.get("description") or "forecast unavailable",
        weather_icon=weather.get("icon"),
        risk_level=risk_level,
        senior_advice=_senior_advice(risk_level),
    )
