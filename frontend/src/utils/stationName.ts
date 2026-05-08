/**
 * Helpers for resolving station names that come from third-party route data
 * (Google Directions) into queries our local DB / scraped CSV can match.
 *
 * Two transformations are needed:
 *
 * 1. Extracting a station name out of free-form instruction text. Walking
 *    steps from Google Directions usually arrive without a populated
 *    `to_station` field, so we fall back to parsing patterns such as
 *    "Walk to KL Sentral" or "Arrive at Pasar Seni".
 *
 * 2. Stripping Malay-language transit prefixes (e.g. "Stesen BRT
 *    Sunu-Monash" -> "Sunu-Monash") and parenthesised qualifiers so the
 *    /locations/search endpoint, which uses ILIKE %query%, finds a match
 *    against the canonical English-style names stored in our database.
 */

const MALAY_PREFIX = /^(stesen|stn\.?)\s+(brt|lrt|mrt|ktm|monorel|monorail)?\s*/i;
const STANDALONE_STESEN = /^stesen\s+/i;

/**
 * Try to derive a station-like reference from a route step instruction. We
 * deliberately keep this conservative: only well-known Google Directions
 * patterns map to a station; anything else returns null so the UI can hide
 * the "view station details" affordance.
 */
export function extractStationNameFromInstruction(instruction: string | null | undefined): string | null {
  if (!instruction) return null;
  const trimmed = instruction.trim();
  // "Walk to <STATION>" — the most common case for first/transfer steps.
  const walkMatch = trimmed.match(/^walk to (.+?)\.?$/i);
  if (walkMatch) return walkMatch[1].trim();
  // "Arrive at <STATION>." — final-step verbiage when destination is a stop.
  const arriveMatch = trimmed.match(/^arrive at (.+?)\.?$/i);
  if (arriveMatch) return arriveMatch[1].trim();
  return null;
}

/**
 * Normalize a station name for backend search. The /locations/search route
 * uses ILIKE %query%, so we want to keep the most distinctive part of the
 * name and drop transit-mode prefixes / bracketed annotations / trailing
 * locality suffixes that our DB rows do not include.
 */
export function cleanStationQuery(raw: string | null | undefined): string {
  if (!raw) return '';
  let name = raw.trim();
  // Strip Malay transit prefixes: "Stesen BRT Sunu-Monash" -> "Sunu-Monash".
  name = name.replace(MALAY_PREFIX, '').trim();
  name = name.replace(STANDALONE_STESEN, '').trim();
  // Drop parenthesised qualifiers like "(MRT)" or "(stop)".
  name = name.replace(/\s*\([^)]*\)\s*/g, ' ').trim();
  // Drop trailing locality suffixes ("KL Sentral, Brickfields" -> "KL Sentral").
  if (name.includes(',')) {
    const head = name.split(',')[0].trim();
    if (head) name = head;
  }
  return name.replace(/\s+/g, ' ').trim();
}
