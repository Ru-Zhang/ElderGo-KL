import { apiRequest } from './api';

export interface DestinationWeather {
  destinationName: string;
  forecastTime: string;
  periodLabel: 'now' | 'morning' | 'afternoon' | 'evening';
  temperatureC: number;
  feelsLikeC: number;
  humidityPercent?: number | null;
  rainMm: number;
  precipitationProbabilityPercent?: number | null;
  windKmh: number;
  weatherMain: string;
  weatherDescription: string;
  weatherIcon?: string | null;
  riskLevel: 'clear' | 'rain' | 'hot' | 'storm' | 'unavailable';
  seniorAdvice: string[];
}

export interface WeatherForecastRequest {
  destinationName: string;
  lat?: number | null;
  lon?: number | null;
  departureTime: 'now' | 'morning' | 'afternoon' | 'evening';
}

interface ApiWeatherForecastResponse {
  destination_name: string;
  forecast_time: string;
  period_label: 'now' | 'morning' | 'afternoon' | 'evening';
  temperature_c: number;
  feels_like_c: number;
  humidity_percent?: number | null;
  rain_mm: number;
  precipitation_probability_percent?: number | null;
  wind_kmh: number;
  weather_main: string;
  weather_description: string;
  weather_icon?: string | null;
  risk_level: 'clear' | 'rain' | 'hot' | 'storm' | 'unavailable';
  senior_advice: string[];
}

export async function getDestinationWeather(request: WeatherForecastRequest): Promise<DestinationWeather> {
  // Translate frontend request fields into backend contract keys.
  const body = await apiRequest<ApiWeatherForecastResponse>('/weather/forecast', {
    method: 'POST',
    body: JSON.stringify({
      destination_name: request.destinationName,
      lat: request.lat,
      lon: request.lon,
      departure_time: request.departureTime
    })
  });
  // Normalize response back to frontend camelCase for view components.
  return {
    destinationName: body.destination_name,
    forecastTime: body.forecast_time,
    periodLabel: body.period_label,
    temperatureC: body.temperature_c,
    feelsLikeC: body.feels_like_c,
    humidityPercent: body.humidity_percent,
    rainMm: body.rain_mm,
    precipitationProbabilityPercent: body.precipitation_probability_percent,
    windKmh: body.wind_kmh,
    weatherMain: body.weather_main,
    weatherDescription: body.weather_description,
    weatherIcon: body.weather_icon,
    riskLevel: body.risk_level,
    seniorAdvice: body.senior_advice
  };
}
