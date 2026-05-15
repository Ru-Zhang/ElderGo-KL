import type { NavigationWaypoint } from '../types/routes';

export interface MapsNavigationPoint {
  label: string;
}

export interface BuildMapsDirectionsUrlOptions {
  origin: MapsNavigationPoint;
  destination: MapsNavigationPoint;
  waypoints?: NavigationWaypoint[];
  travelMode?: 'transit' | 'walking' | 'driving' | 'bicycling';
  dirAction?: 'navigate';
}

function formatCoordinate(lat: number, lon: number): string {
  return `${lat},${lon}`;
}

export function formatMapsNavigationPoint(point: MapsNavigationPoint): string {
  return point.label;
}

export function formatNavigationWaypoint(waypoint: NavigationWaypoint): string {
  return formatCoordinate(waypoint.lat, waypoint.lon);
}

export function buildMapsDirectionsUrl({
  origin,
  destination,
  waypoints = [],
  travelMode = 'transit',
  dirAction = 'navigate',
}: BuildMapsDirectionsUrlOptions): string {
  const params = new URLSearchParams({
    api: '1',
    origin: formatMapsNavigationPoint(origin),
    destination: formatMapsNavigationPoint(destination),
    travelmode: travelMode,
    dir_action: dirAction,
  });

  if (waypoints.length > 0) {
    params.set(
      'waypoints',
      waypoints.map((waypoint) => formatNavigationWaypoint(waypoint)).join('|'),
    );
  }

  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function buildAndroidMapsIntentUrl(mapsUrl: string): string {
  const pathAndQuery = mapsUrl.replace(/^https?:\/\//, '');
  return `intent://${pathAndQuery}#Intent;scheme=https;package=com.google.android.apps.maps;end`;
}

export function isMobileBrowser(userAgent: string, maxTouchPoints: number): boolean {
  return (
    /Android|iPhone|iPad|iPod/i.test(userAgent) ||
    (maxTouchPoints > 1 && /Macintosh/i.test(userAgent))
  );
}
