import { LocationDetail, LocationSummary } from '../types/locations';
import { apiRequest } from './api';

export async function getPopularLocations(): Promise<LocationSummary[]> {
  return apiRequest<LocationSummary[]>('/locations/popular');
}

export async function searchLocations(query: string): Promise<LocationSummary[]> {
  if (!query.trim()) return [];
  return apiRequest<LocationSummary[]>(`/locations/search?q=${encodeURIComponent(query)}`);
}

export async function getLocationDetail(locationId: string): Promise<LocationDetail | null> {
  return apiRequest<LocationDetail>(`/locations/${encodeURIComponent(locationId)}`);
}
