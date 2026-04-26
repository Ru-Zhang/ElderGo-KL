export type AccessibilityStatus = 'supported' | 'limited' | 'unknown' | 'not_verified';
export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'unknown';

export interface LocationSummary {
  id: string;
  name: string;
  type: 'rail_station' | 'accessibility_point' | 'place';
  lat?: number | null;
  lon?: number | null;
  accessibility_status: AccessibilityStatus;
  confidence: ConfidenceLevel;
  note?: string | null;
}

export interface LocationDetail extends LocationSummary {
  routes: string[];
  known_facilities: string[];
  source_list: string[];
}

export interface PlaceSelection {
  displayName: string;
  lat?: number | null;
  lon?: number | null;
  googlePlaceId?: string | null;
}
