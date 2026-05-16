import { apiRequest } from './api';
import { normalizeDepartureKey } from '../utils/departureTime';

export type DeparturePeriod =
  | 'now'
  | 'morning_peak'
  | 'midday'
  | 'evening_peak'
  | 'night'
  | 'morning'
  | 'afternoon'
  | 'evening';

export interface WeatherHourlySlot {
  forecastTime: string;
  temperatureC: number;
  feelsLikeC: number;
  weatherDescription: string;
  precipitationProbabilityPercent?: number | null;
  isDepartureWindow: boolean;
}

export interface DestinationWeather {
  destinationName: string;
  forecastTime: string;
  periodLabel: string;
  departureForecastLabel?: string | null;
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
  rainPeriodStart?: string | null;
  rainPeriodEnd?: string | null;
  rainWindowHours?: number | null;
  peakPopPercent?: number | null;
  hourlyOutlook: WeatherHourlySlot[];
}

export interface WeatherForecastRequest {
  destinationName: string;
  lat?: number | null;
  lon?: number | null;
  departureTime: string;
}

interface ApiWeatherForecastResponse {
  destination_name: string;
  forecast_time: string;
  period_label: string;
  departure_forecast_label?: string | null;
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
  rain_period_start?: string | null;
  rain_period_end?: string | null;
  rain_window_hours?: number | null;
  peak_pop_percent?: number | null;
  hourly_outlook?: Array<{
    forecast_time: string;
    temperature_c: number;
    feels_like_c: number;
    weather_description: string;
    precipitation_probability_percent?: number | null;
    is_departure_window?: boolean;
  }>;
}

const WEATHER_CACHE_TTL_MS = 10 * 60 * 1000;
const weatherCache = new Map<string, { at: number; data: DestinationWeather }>();

function weatherCacheKey(request: WeatherForecastRequest): string {
  const lat = typeof request.lat === 'number' ? request.lat.toFixed(4) : 'na';
  const lon = typeof request.lon === 'number' ? request.lon.toFixed(4) : 'na';
  const name = request.destinationName.trim().toLowerCase();
  const departure = normalizeDepartureKey(request.departureTime);
  return `${name}|${lat}|${lon}|${departure}`;
}

function mapWeatherResponse(body: ApiWeatherForecastResponse): DestinationWeather {
  return {
    destinationName: body.destination_name,
    forecastTime: body.forecast_time,
    periodLabel: body.period_label,
    departureForecastLabel: body.departure_forecast_label,
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
    seniorAdvice: body.senior_advice,
    rainPeriodStart: body.rain_period_start,
    rainPeriodEnd: body.rain_period_end,
    rainWindowHours: body.rain_window_hours,
    peakPopPercent: body.peak_pop_percent,
    hourlyOutlook: (body.hourly_outlook ?? []).map((slot) => ({
      forecastTime: slot.forecast_time,
      temperatureC: slot.temperature_c,
      feelsLikeC: slot.feels_like_c,
      weatherDescription: slot.weather_description,
      precipitationProbabilityPercent: slot.precipitation_probability_percent,
      isDepartureWindow: Boolean(slot.is_departure_window),
    })),
  };
}

export async function getDestinationWeather(request: WeatherForecastRequest): Promise<DestinationWeather> {
  const key = weatherCacheKey(request);
  const cached = weatherCache.get(key);
  const now = Date.now();
  if (cached && now - cached.at < WEATHER_CACHE_TTL_MS) {
    return cached.data;
  }

  const body = await apiRequest<ApiWeatherForecastResponse>('/weather/forecast', {
    method: 'POST',
    body: JSON.stringify({
      destination_name: request.destinationName,
      lat: request.lat,
      lon: request.lon,
      departure_time: request.departureTime,
    }),
  });
  const data = mapWeatherResponse(body);
  weatherCache.set(key, { at: now, data });
  return data;
}
