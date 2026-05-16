import { buildRouteKey } from './routeStationImages';

/** Must match backend CANONICAL_CORRIDOR_ROUTE_KEY in route_segment_image_matcher.py */
export const CANONICAL_KLCC_MONASH_ROUTE_KEY = 'klcc|monash university malaysia';

export function isCuratedCorridorRoute(origin: string, destination: string): boolean {
  return buildRouteKey(origin, destination) === CANONICAL_KLCC_MONASH_ROUTE_KEY;
}
