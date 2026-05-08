/**
 * Categorize scraped station facility labels by relevance to elderly users.
 *
 * Tier 1 (mobility) covers items that directly affect whether an elderly user
 * can physically navigate the station (lifts, ramps, etc.). Tier 2 (comfort)
 * covers facilities they actively look for to feel safe and rested (toilets,
 * customer service, prayer rooms). Tier 3 is everything else and stays in
 * the default chip style.
 */

export type FacilityTier = 1 | 2 | 3;

const MOBILITY_PATTERNS = [
  /\blift\b/i,
  /\belevator\b/i,
  /\bescalator\b/i,
  /\bramp\b/i,
  /tactile/i,
  /wheelchair/i,
  /accessible/i,
];

const COMFORT_PATTERNS = [
  /toilet/i,
  /surau/i,
  /shelter/i,
  /\bcovered\b/i,
  /customer service/i,
  /information/i,
  /rest area/i,
  /seat/i,
  /bench/i,
];

export function getFacilityTier(label: string): FacilityTier {
  if (MOBILITY_PATTERNS.some((p) => p.test(label))) return 1;
  if (COMFORT_PATTERNS.some((p) => p.test(label))) return 2;
  return 3;
}

/**
 * Returns facilities reordered as tier 1 -> tier 2 -> tier 3.
 * Within each tier the original order is preserved so the source data is
 * still recognizable to maintainers.
 */
export function sortFacilitiesForElders(items: string[]): string[] {
  return [...items]
    .map((value, index) => ({ value, index, tier: getFacilityTier(value) }))
    .sort((a, b) => (a.tier !== b.tier ? a.tier - b.tier : a.index - b.index))
    .map((entry) => entry.value);
}

/** Mobility + comfort tiers only — used on compact route step cards. */
export function getElderHighlightFacilities(items: string[]): string[] {
  return sortFacilitiesForElders(items).filter((label) => getFacilityTier(label) <= 2);
}
