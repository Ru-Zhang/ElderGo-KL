import { LocationDetail, LocationSummary } from '../types/locations';
import { apiRequest } from './api';

export async function getPopularLocations(): Promise<LocationSummary[]> {
  return apiRequest<LocationSummary[]>('/locations/popular');
}

export async function searchLocations(query: string): Promise<LocationSummary[]> {
  // Mirror backend behavior for blank input to avoid unnecessary network calls
  // while users are clearing the search box.
  if (!query.trim()) return [];
  return apiRequest<LocationSummary[]>(`/locations/search?q=${encodeURIComponent(query)}`);
}

export async function getLocationDetail(locationId: string): Promise<LocationDetail | null> {
  return apiRequest<LocationDetail>(`/locations/${encodeURIComponent(locationId)}`);
}
