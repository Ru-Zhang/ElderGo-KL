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

function normalizeFacilityLabel(label: string): string {
  return label.toLowerCase().replace(/\s+/g, ' ').trim();
}

/** Drop near-duplicate labels (e.g. "Shops" when "Shops & Mall" is present). */
export function dedupeFacilities(items: string[]): string[] {
  const ordered = sortFacilitiesForElders(items);
  const kept: string[] = [];

  for (const item of ordered) {
    const norm = normalizeFacilityLabel(item);
    const supersededIdx = kept.findIndex((existing) => {
      const existingNorm = normalizeFacilityLabel(existing);
      if (norm === existingNorm) return true;
      return existingNorm.length > norm.length + 2 && existingNorm.includes(norm);
    });
    if (supersededIdx >= 0) continue;

    const withoutShorter = kept.filter((existing) => {
      const existingNorm = normalizeFacilityLabel(existing);
      return !(norm.length > existingNorm.length + 2 && norm.includes(existingNorm));
    });

    kept.length = 0;
    kept.push(...withoutShorter, item);
  }

  return kept;
}

export function prepareFacilitiesForDisplay(items: string[]): string[] {
  return dedupeFacilities(items);
}

/** Mobility + comfort tiers only — used on compact route step cards. */
export function getElderHighlightFacilities(items: string[]): string[] {
  return sortFacilitiesForElders(items).filter((label) => getFacilityTier(label) <= 2);
}
