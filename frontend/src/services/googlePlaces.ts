import { PlaceSelection } from '../types/locations';
import {
  formatPlaceDisplayName,
  normalizePlaceText,
  placeTextsMatch,
} from '../utils/placeDisplay';
import { apiRequest } from './api';
import { API_BASE_URL } from './api';

export interface GooglePlaceDetail {
  display_name: string;
  google_place_id: string;
  lat?: number | null;
  lon?: number | null;
  name?: string | null;
  formatted_address?: string | null;
  rating?: number | null;
  user_ratings_total?: number | null;
  website?: string | null;
  phone_number?: string | null;
  opening_hours: string[];
}

export async function getPlaceSuggestions(query: string): Promise<PlaceSelection[]> {
  if (!query.trim()) return [];
  const suggestions = await apiRequest<Array<{
    description: string;
    place_id: string;
    main_text?: string | null;
  }>>(
    `/places/autocomplete?q=${encodeURIComponent(query)}`
  );
  // Prefer `main_text` so dropdown stays concise and readable on mobile.
  return suggestions.map((suggestion) => ({
    displayName: suggestion.main_text?.trim() || suggestion.description,
    googlePlaceId: suggestion.place_id
  }));
}

export function placeDetailToSelection(
  detail: {
    display_name: string;
    google_place_id: string;
    lat?: number | null;
    lon?: number | null;
    name?: string | null;
  },
  preferredLabel?: string | null
): PlaceSelection {
  const rawLabel = preferredLabel?.trim() || detail.name?.trim() || detail.display_name;
  const selection = {
    displayName: formatPlaceDisplayName(rawLabel),
    googlePlaceId: detail.google_place_id,
    lat: detail.lat,
    lon: detail.lon,
  };
  // #region agent log
  fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
    body: JSON.stringify({
      sessionId: 'ce83c2',
      hypothesisId: 'H-A',
      location: 'googlePlaces.ts:placeDetailToSelection',
      message: 'place_label_mapped',
      data: {
        preferredLabel: preferredLabel ?? null,
        googleName: detail.name ?? null,
        displayName: selection.displayName,
      },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
  return selection;
}

export async function getPlaceDetail(
  placeId: string,
  preferredLabel?: string | null
): Promise<PlaceSelection> {
  const detail = await apiRequest<{
    display_name: string;
    google_place_id: string;
    lat?: number | null;
    lon?: number | null;
    name?: string | null;
  }>(`/places/details/${encodeURIComponent(placeId)}`);
  return placeDetailToSelection(detail, preferredLabel);
}

/** Resolve station or free-text prefill to a confirmed Google place (case-insensitive). */
export async function resolvePlaceSelection(place: PlaceSelection): Promise<PlaceSelection> {
  if (place.googlePlaceId) {
    try {
      return await getPlaceDetail(place.googlePlaceId, place.displayName);
    } catch {
      return {
        ...place,
        displayName: formatPlaceDisplayName(place.displayName),
      };
    }
  }

  if (place.lat != null && place.lon != null && place.displayName.trim()) {
    try {
      const detail = await getStationGooglePlaceDetail(
        place.displayName,
        place.lat,
        place.lon,
      );
      return placeDetailToSelection(detail);
    } catch {
      return {
        ...place,
        displayName: formatPlaceDisplayName(place.displayName),
      };
    }
  }

  const query = place.displayName.trim();
  if (!query) {
    return place;
  }

  try {
    const suggestions = await getPlaceSuggestions(query);
    const normalizedQuery = normalizePlaceText(query);
    const exactMatch = suggestions.find((suggestion) => {
      const short = formatPlaceDisplayName(suggestion.displayName);
      return (
        placeTextsMatch(short, query) ||
        placeTextsMatch(suggestion.displayName, query) ||
        normalizePlaceText(short) === normalizedQuery
      );
    });

    if (exactMatch?.googlePlaceId) {
      return await getPlaceDetail(
        exactMatch.googlePlaceId,
        formatPlaceDisplayName(exactMatch.displayName)
      );
    }
  } catch {
    // Keep original prefill when Places is unavailable.
  }

  return {
    ...place,
    displayName: formatPlaceDisplayName(place.displayName),
  };
}

export async function getStationGooglePlaceDetail(
  name: string,
  lat?: number | null,
  lon?: number | null
): Promise<GooglePlaceDetail> {
  const params = new URLSearchParams({ name });
  if (lat !== null && lat !== undefined) params.set('lat', String(lat));
  if (lon !== null && lon !== undefined) params.set('lon', String(lon));
  return apiRequest<GooglePlaceDetail>(`/places/station-detail?${params.toString()}`);
}

export function getStationStaticImageUrl(
  name: string,
  lat?: number | null,
  lon?: number | null
): string {
  // Build backend proxied image URL to avoid exposing third-party photo keys in client.
  const params = new URLSearchParams({ name });
  if (lat !== null && lat !== undefined) params.set('lat', String(lat));
  if (lon !== null && lon !== undefined) params.set('lon', String(lon));
  return `${API_BASE_URL}/places/station-image?${params.toString()}`;
}
