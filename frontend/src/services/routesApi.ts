import { RecommendedRoute, RouteRecommendationRequest, toApiRouteRequest } from '../types/routes';
import { apiRequest } from './api';
import {
  buildRouteCacheKey,
  routeCacheTtlMs,
  ROUTE_CACHE_MAX_ENTRIES,
} from '../utils/routeCacheKey';

const routeCache = new Map<
  string,
  { at: number; route: RecommendedRoute; departureTime: string }
>();

function pruneRouteCache() {
  const now = Date.now();
  for (const [key, entry] of routeCache.entries()) {
    if (now - entry.at > routeCacheTtlMs(entry.departureTime)) {
      routeCache.delete(key);
    }
  }
  while (routeCache.size > ROUTE_CACHE_MAX_ENTRIES) {
    const oldest = routeCache.keys().next().value;
    if (oldest) routeCache.delete(oldest);
  }
}

export function getCachedRoute(request: RouteRecommendationRequest): RecommendedRoute | null {
  const key = buildRouteCacheKey(request);
  const entry = routeCache.get(key);
  if (!entry) return null;
  const ttl = routeCacheTtlMs(entry.departureTime);
  if (Date.now() - entry.at > ttl) {
    routeCache.delete(key);
    return null;
  }
  routeCache.delete(key);
  routeCache.set(key, entry);
  return entry.route;
}

export function setCachedRoute(request: RouteRecommendationRequest, route: RecommendedRoute): void {
  const key = buildRouteCacheKey(request);
  routeCache.set(key, { at: Date.now(), route, departureTime: request.departureTime });
  pruneRouteCache();
}

/** Preferences changed — drop cached routes so the next plan uses fresh prefs. */
export function clearRouteCache(): void {
  routeCache.clear();
}

export async function recommendRoute(
  request: RouteRecommendationRequest,
  signal?: AbortSignal,
): Promise<RecommendedRoute> {
  if (!signal?.aborted) {
    const cached = getCachedRoute(request);
    if (cached) {
      return cached;
    }
  }

  const route = await apiRequest<RecommendedRoute>('/routes/recommend', {
    method: 'POST',
    body: JSON.stringify(toApiRouteRequest(request)),
    signal,
  });

  if (!signal?.aborted) {
    setCachedRoute(request, route);
  }
  return route;
}
