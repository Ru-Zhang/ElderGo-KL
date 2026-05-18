import { normalizeRouteKeyPart } from './routeStationImages';

/** Must match backend CANONICAL_CORRIDOR_ROUTE_KEY in curated_corridor_policy.py */
export const CANONICAL_KLCC_MONASH_ROUTE_KEY = 'klcc|monash university malaysia';

export function isKlccPlace(name: string | null | undefined): boolean {
  const normalized = normalizeRouteKeyPart(name ?? '');
  if (!normalized) return false;
  if (normalized === 'klcc' || normalized.startsWith('klcc ')) return true;
  if (normalized.includes('klcc lrt') || normalized.includes('lrt klcc')) return true;
  if (normalized.includes('suria') && normalized.includes('klcc')) return true;
  return false;
}

export function isMonashPlace(name: string | null | undefined): boolean {
  return normalizeRouteKeyPart(name ?? '').includes('monash');
}

/** Only KLCC → Monash uses backend/data route_*.csv; all other trips use Google defaults. */
export function isCuratedCorridorRoute(origin: string, destination: string): boolean {
  return isKlccPlace(origin) && isMonashPlace(destination) && !isMonashPlace(origin);
}
