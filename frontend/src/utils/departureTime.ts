/** KL public-transit departure presets — mirrors backend departure_time_service.py */

export type DeparturePreset =
  | 'now'
  | 'morning_peak'
  | 'midday'
  | 'evening_peak'
  | 'night';

export type DepartureSelection = DeparturePreset | 'custom';

const PRESET_TIMES: Record<Exclude<DeparturePreset, 'now'>, [number, number]> = {
  morning_peak: [7, 30],
  midday: [12, 0],
  evening_peak: [18, 0],
  night: [21, 30],
};

const LEGACY_KEY_MAP: Record<string, DeparturePreset> = {
  morning: 'morning_peak',
  afternoon: 'midday',
  evening: 'night',
};

const SERVICE_START_MINUTES = 6 * 60;
const SERVICE_END_MINUTES = 23 * 60 + 30;
/** Latest minute selectable in the custom picker (5-minute steps). */
export const PICKER_END_MINUTES = 23 * 60 + 55;

export function normalizeDepartureKey(value: string): DeparturePreset | string {
  const lowered = value.trim().toLowerCase();
  if (lowered in LEGACY_KEY_MAP) {
    return LEGACY_KEY_MAP[lowered];
  }
  if (lowered === 'now' || lowered in PRESET_TIMES) {
    return lowered as DeparturePreset;
  }
  return value.trim();
}

function klNow(): Date {
  return new Date();
}

function toKlParts(date: Date): { year: number; month: number; day: number; hour: number; minute: number } {
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Kuala_Lumpur',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
  const parts = formatter.formatToParts(date);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value || 0);
  return {
    year: get('year'),
    month: get('month'),
    day: get('day'),
    hour: get('hour'),
    minute: get('minute'),
  };
}

function klDateFromParts(year: number, month: number, day: number, hour: number, minute: number): Date {
  // Build UTC instant for KL local wall time (UTC+8, no DST).
  return new Date(Date.UTC(year, month - 1, day, hour - 8, minute, 0, 0));
}

function clampToServiceHours(klDate: Date): Date {
  const { year, month, day, hour, minute } = toKlParts(klDate);
  const minutes = hour * 60 + minute;
  if (minutes < SERVICE_START_MINUTES) {
    return klDateFromParts(year, month, day, 6, 0);
  }
  if (minutes > SERVICE_END_MINUTES) {
    const next = new Date(klDate.getTime() + 24 * 60 * 60 * 1000);
    const nextParts = toKlParts(next);
    return klDateFromParts(nextParts.year, nextParts.month, nextParts.day, 6, 0);
  }
  return klDate;
}

function nextPresetOccurrence(hour: number, minute: number, from: Date = klNow()): Date {
  const { year, month, day } = toKlParts(from);
  let candidate = klDateFromParts(year, month, day, hour, minute);
  if (candidate.getTime() <= from.getTime()) {
    const tomorrow = new Date(from.getTime() + 24 * 60 * 60 * 1000);
    const t = toKlParts(tomorrow);
    candidate = klDateFromParts(t.year, t.month, t.day, hour, minute);
  }
  return clampToServiceHours(candidate);
}

export function resolveDepartureDate(preset: DeparturePreset | string, customIso?: string): Date {
  if (customIso) {
    return clampToServiceHours(new Date(customIso));
  }
  const normalized = normalizeDepartureKey(preset);
  if (normalized === 'now') {
    return klNow();
  }
  if (typeof normalized === 'string' && normalized in PRESET_TIMES) {
    const [h, m] = PRESET_TIMES[normalized as Exclude<DeparturePreset, 'now'>];
    return nextPresetOccurrence(h, m);
  }
  if (preset.includes('T')) {
    return clampToServiceHours(new Date(preset));
  }
  return klNow();
}

export function formatDeparturePreview(
  preset: DeparturePreset | string,
  language: 'EN' | 'BM',
  customIso?: string
): string {
  const date = resolveDepartureDate(preset, customIso);
  const locale = language === 'BM' ? 'ms-MY' : 'en-MY';
  return new Intl.DateTimeFormat(locale, {
    timeZone: 'Asia/Kuala_Lumpur',
    weekday: 'short',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

function sameKlCalendarDay(a: Date, b: Date): boolean {
  const pa = toKlParts(a);
  const pb = toKlParts(b);
  return pa.year === pb.year && pa.month === pb.month && pa.day === pb.day;
}

function addKlDays(from: Date, days: number): Date {
  return new Date(from.getTime() + days * 24 * 60 * 60 * 1000);
}

/** Readable label with Today / Tomorrow / weekday so preset times are unambiguous. */
export function formatDepartureContextLabel(
  preset: DeparturePreset | string,
  language: 'EN' | 'BM',
  customIso?: string,
): string {
  const date = resolveDepartureDate(preset, customIso);
  const now = klNow();
  const locale = language === 'BM' ? 'ms-MY' : 'en-MY';
  const timePart = new Intl.DateTimeFormat(locale, {
    timeZone: 'Asia/Kuala_Lumpur',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);

  const todayLabel = language === 'BM' ? 'Hari ini' : 'Today';
  const tomorrowLabel = language === 'BM' ? 'Esok' : 'Tomorrow';

  if (!customIso && normalizeDepartureKey(preset) === 'now') {
    return `${todayLabel}, ${timePart}`;
  }
  if (sameKlCalendarDay(date, now)) {
    return `${todayLabel}, ${timePart}`;
  }
  if (sameKlCalendarDay(date, addKlDays(now, 1))) {
    return `${tomorrowLabel}, ${timePart}`;
  }
  const dayPart = new Intl.DateTimeFormat(locale, {
    timeZone: 'Asia/Kuala_Lumpur',
    weekday: 'short',
  }).format(date);
  return `${dayPart}, ${timePart}`;
}

/** @deprecated Use formatDepartureContextLabel */
export function formatDeparturePreviewShort(
  preset: DeparturePreset | string,
  language: 'EN' | 'BM',
  customIso?: string,
): string {
  return formatDepartureContextLabel(preset, language, customIso);
}

export function splitDatetimeLocal(value: string): { date: string; time: string } {
  const [datePart, timePart = '12:00'] = value.split('T');
  return { date: datePart, time: timePart.slice(0, 5) };
}

export function joinDatetimeLocal(date: string, time: string): string {
  return `${date}T${time}`;
}

export function minDateLocal(): string {
  return splitDatetimeLocal(minDatetimeLocal()).date;
}

export function maxDateLocal(): string {
  return splitDatetimeLocal(maxDatetimeLocal()).date;
}

export function minTimeLocalForDate(date: string): string {
  const today = splitDatetimeLocal(minDatetimeLocal()).date;
  if (date === today) {
    return splitDatetimeLocal(minDatetimeLocal()).time;
  }
  return '06:00';
}

export function maxTimeLocalForDate(date: string): string {
  const maxDate = splitDatetimeLocal(maxDatetimeLocal()).date;
  if (date === maxDate) {
    return splitDatetimeLocal(maxDatetimeLocal()).time;
  }
  return '23:55';
}

export function isOutsideTransitServiceHours(value: string): boolean {
  const { time } = splitDatetimeLocal(value);
  const [hourStr, minuteStr] = time.split(':');
  const minutes = Number(hourStr) * 60 + Number(minuteStr);
  return minutes < SERVICE_START_MINUTES || minutes > SERVICE_END_MINUTES;
}

export function toDatetimeLocalValue(date: Date): string {
  const { year, month, day, hour, minute } = toKlParts(date);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${year}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}`;
}

export function datetimeLocalToIso(value: string): string {
  const [datePart, timePart] = value.split('T');
  const time = timePart.length === 5 ? `${timePart}:00` : timePart;
  return `${datePart}T${time}+08:00`;
}

export function departureValueForApi(
  selection: DepartureSelection,
  customDatetimeLocal?: string
): string {
  if (selection === 'custom' && customDatetimeLocal) {
    return datetimeLocalToIso(customDatetimeLocal);
  }
  return selection;
}

export const DEPARTURE_PRESETS: DeparturePreset[] = [
  'now',
  'morning_peak',
  'midday',
  'evening_peak',
  'night',
];

/** Earliest selectable custom time — current KL moment (Google allows now and future). */
export function minDatetimeLocal(): string {
  return toDatetimeLocalValue(klNow());
}

/** Latest selectable custom time — service end on a day up to `daysAhead` in the future. */
export function maxDatetimeLocal(daysAhead = 7): string {
  const future = new Date(klNow().getTime() + daysAhead * 24 * 60 * 60 * 1000);
  const { year, month, day } = toKlParts(future);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${year}-${pad(month)}-${pad(day)}T23:55`;
}

export function clampDatetimeLocal(value: string): string {
  const min = minDatetimeLocal();
  const max = maxDatetimeLocal();
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

/** Align custom picker value with transit service hours (06:00–23:30 KL). */
export function clampDatetimeLocalToServiceHours(value: string): string {
  const bounded = clampDatetimeLocal(value);
  const iso = datetimeLocalToIso(bounded);
  return toDatetimeLocalValue(clampToServiceHours(new Date(iso)));
}

export function isDatetimeLocalInPast(value: string): boolean {
  return value < minDatetimeLocal();
}

const KL_TIMEZONE = 'Asia/Kuala_Lumpur';

export function formatDateLocalDisplay(datePart: string, language: 'EN' | 'BM'): string {
  const iso = `${datePart}T12:00:00+08:00`;
  return new Intl.DateTimeFormat(language === 'BM' ? 'ms-MY' : 'en-MY', {
    timeZone: KL_TIMEZONE,
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso));
}

export function formatTimeLocalDisplay(timePart: string, language: 'EN' | 'BM'): string {
  const iso = `2020-01-01T${timePart}:00+08:00`;
  return new Intl.DateTimeFormat(language === 'BM' ? 'ms-MY' : 'en-MY', {
    timeZone: KL_TIMEZONE,
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(new Date(iso));
}
