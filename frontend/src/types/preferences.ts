export interface TravelPreferences {
  accessibilityFirst: boolean;
  leastWalk: boolean;
  fewestTransfers: boolean;
}

export interface ApiTravelPreferences {
  accessibility_first: boolean;
  least_walk: boolean;
  fewest_transfers: boolean;
}

export function toApiPreferences(preferences: TravelPreferences): ApiTravelPreferences {
  // Boundary mapper between frontend camelCase and backend snake_case.
  return {
    accessibility_first: preferences.accessibilityFirst,
    least_walk: preferences.leastWalk,
    fewest_transfers: preferences.fewestTransfers
  };
}

export function fromApiPreferences(preferences: ApiTravelPreferences): TravelPreferences {
  return {
    accessibilityFirst: preferences.accessibility_first,
    leastWalk: preferences.least_walk,
    fewestTransfers: preferences.fewest_transfers
  };
}
