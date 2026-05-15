import { apiRequest } from './api';

export type RouteStationImage = {
  path: string;
  caption: string;
};

const routeImageMapCache = new Map<string, Record<string, RouteStationImage[]>>();

export async function fetchRouteStationImageMap(
  routeKey: string,
): Promise<Record<string, RouteStationImage[]>> {
  const cached = routeImageMapCache.get(routeKey);
  if (cached) return cached;

  const map = await apiRequest<Record<string, RouteStationImage[]>>(
    `/places/route-station-images?route_key=${encodeURIComponent(routeKey)}`,
  );
  routeImageMapCache.set(routeKey, map);
  return map;
}

export function clearRouteStationImageMapCache(): void {
  routeImageMapCache.clear();
}

export function invalidateRouteStationImageMapCache(routeKey?: string): void {
  if (routeKey) {
    routeImageMapCache.delete(routeKey);
    return;
  }
  routeImageMapCache.clear();
}
