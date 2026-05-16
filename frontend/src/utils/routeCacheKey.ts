import { PlaceSelection } from '../types/locations';
import { TravelPreferences } from '../types/preferences';
import { RouteRecommendationRequest } from '../types/routes';
import { normalizeDepartureKey, resolveDepartureDate } from './departureTime';

function placeKey(place: PlaceSelection): string {
  if (typeof place.lat === 'number' && typeof place.lon === 'number') {
    return `${place.lat.toFixed(4)},${place.lon.toFixed(4)}`;
  }
  if (place.googlePlaceId) {
    return `pid:${place.googlePlaceId}`;
  }
  return `name:${place.displayName.trim().toLowerCase()}`;
}

function preferencesKey(preferences: TravelPreferences): string {
  return `a${preferences.accessibilityFirst ? 1 : 0}w${preferences.leastWalk ? 1 : 0}t${preferences.fewestTransfers ? 1 : 0}`;
}

function departureBucket(departureTime: string): string {
  const normalized = normalizeDepartureKey(departureTime);
  const now = new Date();

  if (normalized === 'now') {
    const bucketMinutes = 5;
    const minute = Math.floor(now.getMinutes() / bucketMinutes) * bucketMinutes;
    const bucket = new Date(now);
    bucket.setMinutes(minute, 0, 0);
    return `now:${bucket.toISOString()}`;
  }

  const isIso =
    normalized.includes('T') ||
    !['morning_peak', 'midday', 'evening_peak', 'night'].includes(normalized as string);

  let resolved: Date;
  if (isIso) {
    resolved = new Date(departureTime.includes('T') ? departureTime : resolveDepartureDate(normalized));
  } else {
    resolved = resolveDepartureDate(normalized);
  }

  const bucketMinutes = 15;
  const minute = Math.floor(resolved.getMinutes() / bucketMinutes) * bucketMinutes;
  const bucket = new Date(resolved);
  bucket.setMinutes(minute, 0, 0);

  if (isIso) {
    return `iso:${bucket.toISOString()}`;
  }
  return `preset:${normalized}:${bucket.toISOString()}`;
}

export function buildRouteCacheKey(request: RouteRecommendationRequest): string {
  return [
    placeKey(request.origin),
    placeKey(request.destination),
    departureBucket(request.departureTime),
    preferencesKey(request.preferences),
  ].join('|');
}

export const ROUTE_CACHE_TTL_MS = 15 * 60 * 1000;
export const ROUTE_CACHE_NOW_TTL_MS = 10 * 60 * 1000;
export const ROUTE_CACHE_MAX_ENTRIES = 8;

export function routeCacheTtlMs(departureTime: string): number {
  return normalizeDepartureKey(departureTime) === 'now' ? ROUTE_CACHE_NOW_TTL_MS : ROUTE_CACHE_TTL_MS;
}
