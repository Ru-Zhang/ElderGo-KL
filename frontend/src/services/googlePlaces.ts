import { PlaceSelection } from '../types/locations';
import { apiRequest } from './api';

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
  const suggestions = await apiRequest<Array<{ description: string; place_id: string }>>(
    `/places/autocomplete?q=${encodeURIComponent(query)}`
  );
  return suggestions.map((suggestion) => ({
    displayName: suggestion.description,
    googlePlaceId: suggestion.place_id
  }));
}

export async function getPlaceDetail(placeId: string): Promise<PlaceSelection> {
  const detail = await apiRequest<{
    display_name: string;
    google_place_id: string;
    lat?: number | null;
    lon?: number | null;
  }>(`/places/details/${encodeURIComponent(placeId)}`);
  return {
    displayName: detail.display_name,
    googlePlaceId: detail.google_place_id,
    lat: detail.lat,
    lon: detail.lon
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
