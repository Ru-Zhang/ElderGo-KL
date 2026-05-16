type RankingFactor = 'walk' | 'accessibility' | 'duration' | 'transfers';

const PRIMARY_KEYS: Record<RankingFactor, string> = {
  walk: 'routeRankingPrimaryWalk',
  accessibility: 'routeRankingPrimaryAccessibility',
  duration: 'routeRankingPrimaryDuration',
  transfers: 'routeRankingPrimaryTransfers',
};

const SECONDARY_KEYS: Record<RankingFactor, string> = {
  walk: 'routeRankingSecondaryWalk',
  accessibility: 'routeRankingSecondaryAccessibility',
  duration: 'routeRankingSecondaryDuration',
  transfers: 'routeRankingSecondaryTransfers',
};

function normalizeFactor(value: string | null | undefined): RankingFactor | null {
  if (!value) return null;
  if (value === 'walk' || value === 'accessibility' || value === 'duration' || value === 'transfers') {
    return value;
  }
  return null;
}

export function rankingFactorTranslationKey(
  factor: string | null | undefined,
  kind: 'primary' | 'secondary',
): string | null {
  const normalized = normalizeFactor(factor);
  if (!normalized) return null;
  return kind === 'primary' ? PRIMARY_KEYS[normalized] : SECONDARY_KEYS[normalized];
}
