import { PlaceSelection } from '../types/locations';

/** Collapse whitespace and lowercase for case-insensitive place matching. */
export function normalizePlaceText(value: string): string {
  return value.trim().replace(/\s+/g, ' ').toLowerCase();
}

export function placeTextsMatch(a: string, b: string): boolean {
  return normalizePlaceText(a) === normalizePlaceText(b);
}

/** Short, human-readable label (station/POI name — not a full street address). */
export function formatPlaceDisplayName(value?: string | null): string {
  if (!value) return '';

  const withoutBrackets = value
    .replace(/\s*\([^)]*\)\s*/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();

  const parts = withoutBrackets
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) return withoutBrackets;
  if (parts.length === 1) return parts[0];

  const firstPart = parts[0];
  if (/[A-Za-z]/.test(firstPart) && !/^\d+$/.test(firstPart)) {
    return firstPart;
  }

  const secondPart = parts[1];
  if (secondPart && /[A-Za-z]/.test(secondPart)) {
    return secondPart;
  }

  return firstPart;
}

export function isPlaceResolved(place: PlaceSelection | null | undefined): boolean {
  if (!place?.displayName?.trim()) return false;
  if (place.googlePlaceId) return true;
  return place.lat != null && place.lon != null;
}

/** True when we should call Google to enrich a prefill (station or chat text). */
export function shouldAutoResolvePlace(place: PlaceSelection | null | undefined): boolean {
  if (!place?.displayName?.trim()) return false;
  return !place.googlePlaceId;
}

/** Chat/text-only prefill with no coordinates — user must confirm from list. */
export function placeSelectionNeedsUserPick(place: PlaceSelection | null | undefined): boolean {
  if (!place?.displayName?.trim()) return false;
  if (place.googlePlaceId) return false;
  if (place.lat != null && place.lon != null) return false;
  return true;
}
