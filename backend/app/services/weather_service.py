from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.weather import (
    DepartureTime,
    WeatherForecastRequest,
    WeatherForecastResponse,
    WeatherHourlySlot,
    WeatherRiskLevel,
)
from app.services.departure_time_service import (
    is_departure_now,
    normalize_departure_key,
    resolve_departure_datetime,
)
from app.services.places_service import get_station_place_detail

OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
OPENWEATHER_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
RAIN_WEATHER_IDS = {500, 501, 502, 503, 504, 511, 520, 521, 522, 531}
FORECAST_SLOT_HOURS = 3
LEAVE_OUTLOOK_HOURS = 3


def _format_departure_forecast_label(target_local: datetime) -> str:
    weekday = target_local.strftime("%a")
    time_part = target_local.strftime("%I:%M %p").lstrip("0")
    return f"{weekday}, {time_part}"


def _select_forecast_item(
    items: list[dict[str, Any]],
    departure_time: str,
    timezone_offset: int,
) -> tuple[dict[str, Any], datetime | None]:
    if not items:
        raise HTTPException(status_code=502, detail="OpenWeatherMap did not return forecast items.")
    normalized = normalize_departure_key(departure_time)
    local_tz = timezone(timedelta(seconds=timezone_offset))
    if is_departure_now(normalized):
        return items[0], None

    target_local = resolve_departure_datetime(normalized).astimezone(local_tz)

    def distance_from_target(item: dict[str, Any]) -> float:
        forecast_local = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(local_tz)
        return abs((forecast_local - target_local).total_seconds())

    return min(items, key=distance_from_target), target_local


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


def _is_wet_forecast(item: dict[str, Any]) -> bool:
    pop = float(item.get("pop") or 0)
    rain_mm = float((item.get("rain") or {}).get("3h") or 0)
    weather_id = int((item.get("weather") or [{}])[0].get("id") or 0)
    return pop >= 0.35 or rain_mm > 0 or weather_id in RAIN_WEATHER_IDS


def _build_hourly_outlook(
    items: list[dict[str, Any]],
    selected: dict[str, Any],
    target_local: datetime | None,
    timezone_offset: int,
    *,
    max_slots: int = 4,
) -> list[WeatherHourlySlot]:
    if not items:
        return []

    local_tz = timezone(timedelta(seconds=timezone_offset))
    slots: list[tuple[datetime, dict[str, Any]]] = []
    for item in items:
        forecast_local = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(local_tz)
        slots.append((forecast_local, item))
    slots.sort(key=lambda entry: entry[0])

    selected_local = datetime.fromtimestamp(selected["dt"], tz=timezone.utc).astimezone(local_tz)
    anchor = target_local or selected_local
    anchor_idx = min(range(len(slots)), key=lambda i: abs((slots[i][0] - anchor).total_seconds()))

    start_idx = anchor_idx
    outlook: list[WeatherHourlySlot] = []
    for idx in range(start_idx, len(slots)):
        if len(outlook) >= max_slots:
            break
        forecast_local, item = slots[idx]
        if idx != anchor_idx:
            hours_after = (forecast_local - anchor).total_seconds() / 3600
            if hours_after <= 0 or hours_after > LEAVE_OUTLOOK_HOURS:
                continue
        if idx != anchor_idx and forecast_local < anchor:
            continue
        main = item.get("main") or {}
        weather = (item.get("weather") or [{}])[0]
        pop = int(round(float(item.get("pop") or 0) * 100))
        outlook.append(
            WeatherHourlySlot(
                forecast_time=forecast_local.isoformat(),
                temperature_c=round(float(main.get("temp") or 0), 1),
                feels_like_c=round(float(main.get("feels_like") or main.get("temp") or 0), 1),
                weather_description=weather.get("description") or "forecast unavailable",
                precipitation_probability_percent=pop or None,
                is_departure_window=idx == anchor_idx,
            )
        )
    return outlook


def _analyze_rain_window(
    items: list[dict[str, Any]],
    selected: dict[str, Any],
    target_local: datetime | None,
    timezone_offset: int,
) -> tuple[str | None, str | None, int | None, int | None]:
    """Summarize likely rain timing from nearby 3-hour OpenWeather slots (ISO local times)."""
    if not items:
        return None, None, None, None

    local_tz = timezone(timedelta(seconds=timezone_offset))
    slots: list[tuple[datetime, dict[str, Any]]] = []
    for item in items:
        forecast_local = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(local_tz)
        slots.append((forecast_local, item))
    slots.sort(key=lambda entry: entry[0])

    selected_local = datetime.fromtimestamp(selected["dt"], tz=timezone.utc).astimezone(local_tz)
    anchor = target_local or selected_local
    anchor_idx = min(range(len(slots)), key=lambda i: abs((slots[i][0] - anchor).total_seconds()))

    wet_flags = [_is_wet_forecast(item) for _, item in slots]
    selected_pop = int(round(float(selected.get("pop") or 0) * 100))

    if not any(wet_flags):
        if selected_pop < 40:
            return None, None, None, selected_pop or None
        start = slots[anchor_idx][0]
        end = start + timedelta(hours=FORECAST_SLOT_HOURS)
        return start.isoformat(), end.isoformat(), FORECAST_SLOT_HOURS, selected_pop

    if not wet_flags[anchor_idx]:
        nearest_wet = min(
            (i for i, wet in enumerate(wet_flags) if wet),
            key=lambda i: abs((slots[i][0] - anchor).total_seconds()),
            default=anchor_idx,
        )
        anchor_idx = nearest_wet

    start_idx = end_idx = anchor_idx
    while start_idx > 0 and wet_flags[start_idx - 1]:
        start_idx -= 1
    while end_idx < len(wet_flags) - 1 and wet_flags[end_idx + 1]:
        end_idx += 1

    start_dt = slots[start_idx][0]
    end_dt = slots[end_idx][0] + timedelta(hours=FORECAST_SLOT_HOURS)
    duration_h = (end_idx - start_idx + 1) * FORECAST_SLOT_HOURS
    peak_pop = max(
        int(round(float(slots[i][1].get("pop") or 0) * 100)) for i in range(start_idx, end_idx + 1)
    )
    return start_dt.isoformat(), end_dt.isoformat(), duration_h, peak_pop


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
    normalized_departure = normalize_departure_key(payload.departure_time)
    timezone_offset = int(city.get("timezone") or 0)
    selected, target_local = _select_forecast_item(items, normalized_departure, timezone_offset)
    departure_forecast_label = _format_departure_forecast_label(target_local) if target_local else None
    main = selected.get("main") or {}
    weather = (selected.get("weather") or [{}])[0]
    wind = selected.get("wind") or {}
    rain = selected.get("rain") or {}
    rain_mm = float(rain.get("3h") or 0)
    wind_kmh = round(float(wind.get("speed") or 0) * 3.6, 1)
    risk_level = _risk_level(selected, rain_mm, wind_kmh)
    rain_start, rain_end, rain_hours, peak_pop = _analyze_rain_window(
        items, selected, target_local, timezone_offset
    )
    hourly_outlook = _build_hourly_outlook(items, selected, target_local, timezone_offset)

    return WeatherForecastResponse(
        destination_name=city.get("name") or payload.destination_name,
        forecast_time=selected.get("dt_txt") or datetime.fromtimestamp(selected["dt"], tz=timezone.utc).isoformat(),
        period_label=normalized_departure,
        departure_forecast_label=departure_forecast_label,
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
        rain_period_start=rain_start,
        rain_period_end=rain_end,
        rain_window_hours=rain_hours,
        peak_pop_percent=peak_pop,
        hourly_outlook=hourly_outlook,
    )
