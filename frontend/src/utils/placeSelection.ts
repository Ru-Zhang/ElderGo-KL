import type { PlaceSelection } from '../types/locations';

/** Ignore internal ElderGo IDs — route API should use coordinates or real Google place IDs. */
export function sanitizeGooglePlaceId(placeId: string | null | undefined): string | null {
  if (!placeId) return null;
  const trimmed = placeId.trim();
  if (trimmed.toLowerCase().startsWith('eldergo:') || trimmed.toLowerCase().startsWith('station:')) {
    return null;
  }
  return trimmed;
}

export function placeSelectionFromChatAction(fields: {
  displayName: string;
  lat?: number | null;
  lon?: number | null;
  googlePlaceId?: string | null;
}): PlaceSelection {
  return {
    displayName: fields.displayName,
    lat: fields.lat ?? null,
    lon: fields.lon ?? null,
    googlePlaceId: sanitizeGooglePlaceId(fields.googlePlaceId),
  };
}
