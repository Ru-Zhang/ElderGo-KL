/**
 * Parse the multi-line `hours_summary` string scraped from mrt.com.my into
 * structured fields the UI can render compactly.
 *
 * Example raw input:
 *   "Station open: 06:00 am
 *    Station closed: 12:00 am (Mon - Sat) / 11:25 pm (Sunday & PH)
 *    Last Train to Gombak: 12:12 am (Mon - Sat) / 11:42 pm (Sunday & PH)
 *    Last Train to Putra Height: 12:07 am (Mon - Sat) / 11:49 pm (Sunday & PH)"
 */

export interface ConditionalTime {
  time: string;
  condition: string;
}

export interface ParsedHours {
  open: ConditionalTime[];
  close: ConditionalTime[];
  lastTrains: { to: string; values: ConditionalTime[] }[];
  other: string[];
}

export function parseHoursSummary(raw: string | null | undefined): ParsedHours | null {
  if (!raw) return null;

  const result: ParsedHours = {
    open: [],
    close: [],
    lastTrains: [],
    other: [],
  };
  const lines = raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (!lines.length) return null;

  for (const line of lines) {
    const colon = line.indexOf(':');
    if (colon < 0) {
      result.other.push(line);
      continue;
    }
    const key = line.slice(0, colon).trim();
    const value = line.slice(colon + 1).trim();

    if (/^station open$/i.test(key)) {
      result.open.push(...splitConditionTime(value));
    } else if (/^station closed$/i.test(key)) {
      result.close.push(...splitConditionTime(value));
    } else if (/^last train to (.+)$/i.test(key)) {
      const m = key.match(/^last train to\s*(.+)$/i);
      const dest = m ? m[1].trim() : key;
      result.lastTrains.push({ to: dest, values: splitConditionTime(value) });
    } else if (/^last train$/i.test(key)) {
      // Some stations (e.g. monorail) show a single "Last train" line with no
      // explicit destination. Surface as an "other" note to avoid misplacing it.
      result.other.push(`${key}: ${value}`);
    } else {
      result.other.push(line);
    }
  }

  if (
    !result.open.length &&
    !result.close.length &&
    !result.lastTrains.length &&
    !result.other.length
  ) {
    return null;
  }
  return result;
}

/**
 * Split values such as "12:00 am (Mon - Sat) / 11:25 pm (Sunday & PH)" into
 * an array of {time, condition} pairs. Falls back to a single entry with
 * empty condition when no parentheses are present.
 */
function splitConditionTime(raw: string): ConditionalTime[] {
  return raw
    .split(/\s*\/\s*/)
    .map((segment) => {
      const trimmed = segment.trim();
      const m = trimmed.match(/^(.+?)\s*\((.+?)\)\s*$/);
      if (m) {
        return { time: normalizeTime(m[1].trim()), condition: normalizeCondition(m[2].trim()) };
      }
      return { time: normalizeTime(trimmed), condition: '' };
    })
    .filter((entry) => entry.time);
}

/**
 * Light normalization: uppercase AM/PM, collapse whitespace.
 * We deliberately avoid converting 12:00 am vs 12:00 midnight semantics —
 * preserving the source string keeps trust in shown values.
 */
function normalizeTime(raw: string): string {
  return raw
    .replace(/\s+/g, ' ')
    .replace(/\b(am|pm)\b/gi, (m) => m.toUpperCase())
    .trim();
}

function normalizeCondition(raw: string): string {
  return raw
    .replace(/\s+/g, ' ')
    .replace(/\bSunday\b/gi, 'Sun')
    .replace(/\bMonday\b/gi, 'Mon')
    .replace(/\b& PH\b/gi, '& PH')
    .trim();
}
