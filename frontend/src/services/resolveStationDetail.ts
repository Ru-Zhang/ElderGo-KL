import type { LocationDetail } from '../types/locations';
import { cleanStationQuery } from '../utils/stationName';
import { getLocationDetail, searchLocations } from './locationsApi';

/**
 * Resolve a free-form station label from route directions into our DB-backed
 * LocationDetail. Mirrors the lookup strategy used by StationDetailModal so
 * step cards and the modal stay consistent.
 */
export async function resolveStationDetailByName(rawName: string): Promise<LocationDetail | null> {
  const cleaned = cleanStationQuery(rawName);
  const queries = Array.from(new Set([cleaned, rawName.trim()].filter(Boolean)));
  for (const q of queries) {
    const matches = await searchLocations(q);
    if (!matches.length) continue;
    const lower = q.toLowerCase();
    const best =
      matches.find((m) => m.name.toLowerCase() === lower) ||
      matches.find((m) => m.name.toLowerCase().startsWith(lower)) ||
      matches.find((m) => m.name.toLowerCase().includes(lower)) ||
      matches[0];
    const fetched = await getLocationDetail(best.id);
    if (fetched) return fetched;
  }
  return null;
}
