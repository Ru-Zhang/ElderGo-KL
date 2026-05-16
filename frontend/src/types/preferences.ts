export type PreferenceFactor = 'accessibility' | 'walk' | 'transfers';

export const DEFAULT_PRIORITY_ORDER: PreferenceFactor[] = ['accessibility', 'walk', 'transfers'];

export interface TravelPreferences {
  accessibilityFirst: boolean;
  leastWalk: boolean;
  fewestTransfers: boolean;
  priorityOrder: PreferenceFactor[];
}

export interface ApiTravelPreferences {
  accessibility_first: boolean;
  least_walk: boolean;
  fewest_transfers: boolean;
  priority_order?: PreferenceFactor[];
}

export function normalizePriorityOrder(value?: PreferenceFactor[] | null): PreferenceFactor[] {
  const normalized: PreferenceFactor[] = [];
  if (Array.isArray(value)) {
    for (const item of value) {
      if (DEFAULT_PRIORITY_ORDER.includes(item) && !normalized.includes(item)) {
        normalized.push(item);
      }
    }
  }
  for (const item of DEFAULT_PRIORITY_ORDER) {
    if (!normalized.includes(item)) normalized.push(item);
  }
  return normalized;
}

export function toApiPreferences(preferences: TravelPreferences): ApiTravelPreferences {
  // Boundary mapper between frontend camelCase and backend snake_case.
  return {
    accessibility_first: preferences.accessibilityFirst,
    least_walk: preferences.leastWalk,
    fewest_transfers: preferences.fewestTransfers,
    priority_order: normalizePriorityOrder(preferences.priorityOrder)
  };
}

export function fromApiPreferences(preferences: ApiTravelPreferences): TravelPreferences {
  return {
    accessibilityFirst: preferences.accessibility_first,
    leastWalk: preferences.least_walk,
    fewestTransfers: preferences.fewest_transfers,
    priorityOrder: normalizePriorityOrder(preferences.priority_order)
  };
}
