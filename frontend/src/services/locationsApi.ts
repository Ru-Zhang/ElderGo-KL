import { getPopularStations, getStationById, searchStations } from '../data/stationsData';
import { LocationDetail, LocationSummary } from '../types/locations';
import { apiRequest } from './api';

function stationToLocation(station: ReturnType<typeof getPopularStations>[number]): LocationSummary {
  return {
    id: station.id,
    name: station.name,
    type: 'rail_station',
    accessibility_status: 'unknown',
    confidence: 'unknown',
    note: 'Demo fallback only. Verify with backend station data before treating as fact.'
  };
}

export async function getPopularLocations(): Promise<LocationSummary[]> {
  try {
    return await apiRequest<LocationSummary[]>('/locations/popular');
  } catch {
    return getPopularStations().map(stationToLocation);
  }
}

export async function searchLocations(query: string): Promise<LocationSummary[]> {
  try {
    return await apiRequest<LocationSummary[]>(`/locations/search?q=${encodeURIComponent(query)}`);
  } catch {
    return searchStations(query).map(stationToLocation);
  }
}

export async function getLocationDetail(locationId: string): Promise<LocationDetail | null> {
  try {
    return await apiRequest<LocationDetail>(`/locations/${encodeURIComponent(locationId)}`);
  } catch {
    const station = getStationById(locationId);
    if (!station) return null;
    return {
      ...stationToLocation(station),
      routes: [],
      known_facilities: [],
      source_list: ['frontend_demo_fallback']
    };
  }
}
