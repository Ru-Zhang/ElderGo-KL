import { LocationDetail, LocationSummary } from '../types/locations';
import { apiRequest } from './api';

const CACHE_TTL_MS = 2 * 60 * 1000;
const searchCache = new Map<string, { at: number; data: LocationSummary[] }>();
const detailCache = new Map<string, { at: number; data: LocationDetail }>();
let popularCache: { at: number; data: LocationSummary[] } | null = null;

export async function getPopularLocations(): Promise<LocationSummary[]> {
  const now = Date.now();
  if (popularCache && now - popularCache.at < CACHE_TTL_MS) {
    return popularCache.data;
  }
  const data = await apiRequest<LocationSummary[]>('/locations/popular');
  popularCache = { at: now, data };
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
    return cached.data;
  }

  const data = await apiRequest<LocationSummary[]>(
    `/locations/search?q=${encodeURIComponent(query)}`,
    init,
  );
  if (!init?.signal) {
    searchCache.set(key, { at: now, data });
  }
  return data;
}

export async function getLocationDetail(
  locationId: string,
  init?: RequestInit,
): Promise<LocationDetail | null> {
  const now = Date.now();
  const cached = detailCache.get(locationId);
  if (cached && now - cached.at < CACHE_TTL_MS && !init?.signal) {
    return cached.data;
  }

  const data = await apiRequest<LocationDetail>(
    `/locations/${encodeURIComponent(locationId)}`,
    init,
  );
  if (!init?.signal) {
    detailCache.set(locationId, { at: now, data });
  }
  return data;
}
