import { PlaceSelection } from './locations';
import { ApiTravelPreferences, TravelPreferences, toApiPreferences } from './preferences';

export interface RouteRecommendationRequest {
  anonymousUserId?: string | null;
  origin: PlaceSelection;
  destination: PlaceSelection;
  departureTime: string;
  preferences: TravelPreferences;
}

export interface ApiRouteRecommendationRequest {
  anonymous_user_id?: string | null;
  origin: {
    display_name: string;
    lat?: number | null;
    lon?: number | null;
    google_place_id?: string | null;
  };
  destination: {
    display_name: string;
    lat?: number | null;
    lon?: number | null;
    google_place_id?: string | null;
  };
  departure_time: string;
  preferences: ApiTravelPreferences;
}

export type RouteStepType = 'walking' | 'transit' | 'arrival';

export interface RouteAccessibilityAnnotation {
  status: 'supported' | 'limited' | 'unknown' | 'not_verified' | 'not_supported';
  message: string;
  source: string;
}

export interface RouteAccessibilityPoint {
  step_number: number;
  point_id: string;
  name?: string | null;
  lat: number;
  lon: number;
  annotation_type: string;
  accessibility_type?: string | null;
  wheelchair?: string | null;
  shelter?: string | null;
  covered?: string | null;
  distance_meters?: number | null;
}

export interface RouteStep {
  step_number: number;
  step_type: RouteStepType;
  instruction: string;
  duration_minutes?: number | null;
  distance_meters?: number | null;
  transit_line?: string | null;
  map_polyline?: string | null;
  transit_color?: string | null;
  transit_vehicle_type?: string | null;
  from_station?: string | null;
  to_station?: string | null;
  annotation: RouteAccessibilityAnnotation;
}

export interface RecommendedRoute {
  recommended_route_id: string;
  origin_name: string;
  destination_name: string;
  duration_minutes: number;
  transfers: number;
  walking_distance_meters: number;
  recommendation_reason: string;
  map_polyline?: string | null;
  steps: RouteStep[];
  accessibility_points?: RouteAccessibilityPoint[];
}

export function toApiRouteRequest(request: RouteRecommendationRequest): ApiRouteRecommendationRequest {
  return {
    anonymous_user_id: request.anonymousUserId,
    origin: {
      display_name: request.origin.displayName,
      lat: request.origin.lat,
      lon: request.origin.lon,
      google_place_id: request.origin.googlePlaceId
    },
    destination: {
      display_name: request.destination.displayName,
      lat: request.destination.lat,
      lon: request.destination.lon,
      google_place_id: request.destination.googlePlaceId
    },
    departure_time: request.departureTime,
    preferences: toApiPreferences(request.preferences)
  };
}
