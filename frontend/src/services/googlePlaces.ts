import { PlaceSelection } from '../types/locations';
import { searchLocations } from './locationsApi';

export async function getPlaceSuggestions(query: string): Promise<PlaceSelection[]> {
  const locations = await searchLocations(query);
  return locations.map((location) => ({
    displayName: location.name,
    lat: location.lat,
    lon: location.lon,
    googlePlaceId: null
  }));
}
