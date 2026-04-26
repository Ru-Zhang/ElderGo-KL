import { PlaceSelection } from '../types/locations';
import { apiRequest } from './api';

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
