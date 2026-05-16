import { LocationDetail, LocationSummary } from '../types/locations';
import { apiRequest } from './api';

const CACHE_TTL_MS = 2 * 60 * 1000;
const searchCache = new Map<string, { at: number; data: LocationSummary[] }>();
const detailCache = new Map<string, { at: number; data: LocationDetail }>();
let popularCache: { at: number; data: LocationSummary[] } | null = null;

function debugLocationLog(message: string, data: Record<string, unknown>, hypothesisId: string) {
  // #region agent log
  fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
    body: JSON.stringify({
      sessionId: 'ce83c2',
      hypothesisId,
      location: 'locationsApi.ts',
      message,
      data,
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
}

export async function getPopularLocations(): Promise<LocationSummary[]> {
  const now = Date.now();
  if (popularCache && now - popularCache.at < CACHE_TTL_MS) {
    debugLocationLog('popular_cache_hit', { count: popularCache.data.length }, 'H8');
    return popularCache.data;
  }
  const started = performance.now();
  const data = await apiRequest<LocationSummary[]>('/locations/popular');
  popularCache = { at: now, data };
  debugLocationLog(
    'popular_fetched',
    { count: data.length, ms: Math.round(performance.now() - started) },
    'H8',
  );
  return data;
}

export async function searchLocations(
  query: string,
  init?: RequestInit,
): Promise<LocationSummary[]> {
  const key = query.trim().toLowerCase();
  if (!key) return [];

  const now = Date.now();
  const cached = searchCache.get(key);
  if (cached && now - cached.at < CACHE_TTL_MS && !init?.signal) {
    debugLocationLog('search_cache_hit', { key, count: cached.data.length }, 'H7');
    return cached.data;
  }

  const started = performance.now();
  const data = await apiRequest<LocationSummary[]>(
    `/locations/search?q=${encodeURIComponent(query)}`,
    init,
  );
  if (!init?.signal) {
    searchCache.set(key, { at: now, data });
  }
  debugLocationLog(
    'search_fetched',
    { key, count: data.length, ms: Math.round(performance.now() - started) },
    'H7',
  );
  return data;
}

export async function getLocationDetail(
  locationId: string,
  init?: RequestInit,
): Promise<LocationDetail | null> {
  const now = Date.now();
  const cached = detailCache.get(locationId);
  if (cached && now - cached.at < CACHE_TTL_MS && !init?.signal) {
    debugLocationLog('detail_cache_hit', { locationId }, 'H7');
    return cached.data;
  }

  const started = performance.now();
  const data = await apiRequest<LocationDetail>(
    `/locations/${encodeURIComponent(locationId)}`,
    init,
  );
  if (!init?.signal) {
    detailCache.set(locationId, { at: now, data });
  }
  debugLocationLog(
    'detail_fetched',
    { locationId, ms: Math.round(performance.now() - started) },
    'H7',
  );
  return data;
}
