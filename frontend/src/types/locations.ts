export type AccessibilityStatus = 'supported' | 'not_supported' | 'unknown';
export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'unknown';

export interface LocationSummary {
  id: string;
  name: string;
  type: string;
  lat?: number | null;
  lon?: number | null;
  accessibility_status: AccessibilityStatus;
  confidence: ConfidenceLevel;
  note?: string | null;
  /** Line short codes (KJL, MRL, ...) populated for rail_station rows. */
  routes?: string[];
}

export interface LocationDetail extends LocationSummary {
  routes: string[];
  known_facilities: string[];
  source_list: string[];
  /** Official station amenities from mrt.com.my scrape (subset of hubs). */
  station_facilities?: string[];
  station_address?: string | null;
  station_hours_summary?: string | null;
  facility_source_url?: string | null;
}

export interface PlaceSelection {
  // Lightweight location shape used across planning flow and API requests.
  displayName: string;
  lat?: number | null;
  lon?: number | null;
  googlePlaceId?: string | null;
}
