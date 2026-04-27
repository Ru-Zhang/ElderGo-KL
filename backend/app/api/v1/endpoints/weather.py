from fastapi import APIRouter

from app.schemas.weather import WeatherForecastRequest, WeatherForecastResponse
from app.services.weather_service import get_weather_forecast

router = APIRouter()


@router.post("/forecast", response_model=WeatherForecastResponse)
async def weather_forecast(payload: WeatherForecastRequest) -> WeatherForecastResponse:
    return await get_weather_forecast(payload)
