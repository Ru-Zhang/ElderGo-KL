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

export const GOOGLE_MAPS_IOS_APP_STORE_URL =
  'https://apps.apple.com/app/google-maps-transit-food/id585027354';
export const GOOGLE_MAPS_ANDROID_PLAY_STORE_URL =
  'https://play.google.com/store/apps/details?id=com.google.android.apps.maps';

export const GOOGLE_MAPS_INSTALLED_SESSION_KEY = 'eldergo_google_maps_available';

const GOOGLE_MAPS_APP_DETECTION_DELAY_MS = 1600;

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
  const fallback = encodeURIComponent(mapsUrl);
  const playStore = encodeURIComponent(GOOGLE_MAPS_ANDROID_PLAY_STORE_URL);
  return (
    `intent://${pathAndQuery}#Intent;` +
    `scheme=https;` +
    `package=com.google.android.apps.maps;` +
    `S.browser_fallback_url=${fallback};` +
    `S.market_referrer=${playStore};` +
    `end`
  );
}

export function buildIosMapsProbeUrl(destinationLabel: string): string {
  const params = new URLSearchParams({
    daddr: destinationLabel,
    directionsmode: 'transit',
  });
  return `comgooglemaps://?${params.toString()}`;
}

export function isMobileBrowser(userAgent: string, maxTouchPoints: number): boolean {
  return (
    /Android|iPhone|iPad|iPod/i.test(userAgent) ||
    (maxTouchPoints > 1 && /Macintosh/i.test(userAgent))
  );
}

export function isIosBrowser(userAgent: string): boolean {
  return /iPhone|iPad|iPod/i.test(userAgent);
}

export function isAndroidBrowser(userAgent: string): boolean {
  return /Android/i.test(userAgent);
}

export function getGoogleMapsStoreUrl(userAgent: string): string {
  if (isIosBrowser(userAgent)) {
    return GOOGLE_MAPS_IOS_APP_STORE_URL;
  }
  return GOOGLE_MAPS_ANDROID_PLAY_STORE_URL;
}

export function markGoogleMapsInstalled(): void {
  try {
    sessionStorage.setItem(GOOGLE_MAPS_INSTALLED_SESSION_KEY, '1');
  } catch {
    // Ignore private browsing storage errors.
  }
}

export function isGoogleMapsMarkedInstalled(): boolean {
  try {
    return sessionStorage.getItem(GOOGLE_MAPS_INSTALLED_SESSION_KEY) === '1';
  } catch {
    return false;
  }
}

export interface OpenGoogleMapsOptions {
  webUrl: string;
  destinationLabel: string;
  userAgent?: string;
  maxTouchPoints?: number;
  onMapsOpened?: () => void;
  onMapsMissing?: () => void;
}

/**
 * Try to open Google Maps on mobile. Calls onMapsOpened when the page loses focus
 * (app likely opened), or onMapsMissing when still visible after a short delay.
 */
export function attemptOpenGoogleMaps({
  webUrl,
  destinationLabel,
  userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : '',
  maxTouchPoints = typeof navigator !== 'undefined' ? navigator.maxTouchPoints : 0,
  onMapsOpened,
  onMapsMissing,
}: OpenGoogleMapsOptions): void {
  if (!isMobileBrowser(userAgent, maxTouchPoints)) {
    window.open(webUrl, '_blank', 'noopener,noreferrer');
    onMapsOpened?.();
    return;
  }

  if (isGoogleMapsMarkedInstalled()) {
    openMapsOnMobile(webUrl, destinationLabel, userAgent);
    onMapsOpened?.();
    return;
  }

  let openedGoogleMaps = false;
  const markOpened = () => {
    openedGoogleMaps = true;
    markGoogleMapsInstalled();
    onMapsOpened?.();
  };
  const cleanup = () => {
    window.removeEventListener('pagehide', markOpened);
    window.removeEventListener('blur', markOpened);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  };
  const handleVisibilityChange = () => {
    if (document.hidden) {
      markOpened();
    }
  };

  window.addEventListener('pagehide', markOpened, { once: true });
  window.addEventListener('blur', markOpened, { once: true });
  document.addEventListener('visibilitychange', handleVisibilityChange);

  openMapsOnMobile(webUrl, destinationLabel, userAgent);

  window.setTimeout(() => {
    cleanup();
    if (!openedGoogleMaps && !document.hidden) {
      onMapsMissing?.();
    }
  }, GOOGLE_MAPS_APP_DETECTION_DELAY_MS);
}

function openMapsOnMobile(webUrl: string, destinationLabel: string, userAgent: string): void {
  if (isAndroidBrowser(userAgent)) {
    window.location.href = buildAndroidMapsIntentUrl(webUrl);
    return;
  }
  if (isIosBrowser(userAgent)) {
    const probeUrl = buildIosMapsProbeUrl(destinationLabel);
    window.location.href = probeUrl;
    window.setTimeout(() => {
      if (!document.hidden) {
        window.location.href = webUrl;
      }
    }, 500);
    return;
  }
  window.location.href = webUrl;
}

export function openGoogleMapsStore(userAgent: string): void {
  window.location.href = getGoogleMapsStoreUrl(userAgent);
}
