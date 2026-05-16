import type { DestinationWeather, WeatherHourlySlot } from '../services/weatherApi';
import type { Language } from '../i18n/translations';
import { getTranslation, type TranslationKey } from '../i18n/translations';

/** Short labels for elderly-friendly UI (EN + BM). */
const SIMPLE_CONDITION: Record<string, { en: string; bm: string }> = {
  'clear sky': { en: 'Clear', bm: 'Cerah' },
  'few clouds': { en: 'Cloudy', bm: 'Berawan' },
  'scattered clouds': { en: 'Cloudy', bm: 'Berawan' },
  'broken clouds': { en: 'Cloudy', bm: 'Berawan' },
  'overcast clouds': { en: 'Cloudy', bm: 'Mendung' },
  'light rain': { en: 'Light rain', bm: 'Hujan renyai' },
  'moderate rain': { en: 'Rain', bm: 'Hujan' },
  'heavy intensity rain': { en: 'Heavy rain', bm: 'Hujan lebat' },
  'very heavy rain': { en: 'Heavy rain', bm: 'Hujan lebat' },
  drizzle: { en: 'Drizzle', bm: 'Renyai' },
  'light intensity drizzle': { en: 'Drizzle', bm: 'Renyai' },
  rain: { en: 'Rain', bm: 'Hujan' },
  thunderstorm: { en: 'Storm', bm: 'Ribut' },
  'thunderstorm with light rain': { en: 'Storm', bm: 'Ribut' },
  'thunderstorm with rain': { en: 'Storm', bm: 'Ribut' },
  mist: { en: 'Misty', bm: 'Jerebu' },
  fog: { en: 'Fog', bm: 'Kabut' },
};

const WEATHER_DESC_BM: Record<string, string> = {
  'clear sky': 'Cerah',
  'few clouds': 'Berawan',
  'scattered clouds': 'Berawan',
  'broken clouds': 'Berawan',
  'overcast clouds': 'Mendung',
  'light rain': 'Hujan renyai',
  'moderate rain': 'Hujan sederhana',
  'heavy intensity rain': 'Hujan lebat',
  'very heavy rain': 'Hujan sangat lebat',
  'light intensity drizzle': 'Renyai',
  'drizzle': 'Renyai',
  'rain': 'Hujan',
  'thunderstorm': 'Ribut petir',
  'thunderstorm with light rain': 'Ribut petir dan hujan renyai',
  'thunderstorm with rain': 'Ribut petir dan hujan',
  mist: 'Jerebu',
  fog: 'Kabut',
};

function normalizeDescKey(value: string): string {
  return value.trim().toLowerCase();
}

export function translateWeatherDescription(description: string, language: Language): string {
  return simplifyWeatherCondition(description, language);
}

export function simplifyWeatherCondition(description: string, language: Language): string {
  if (!description) return '';
  const key = normalizeDescKey(description);
  const simple = SIMPLE_CONDITION[key];
  if (simple) return language === 'BM' ? simple.bm : simple.en;
  if (language === 'BM') {
    return WEATHER_DESC_BM[key] ?? description.charAt(0).toUpperCase() + description.slice(1);
  }
  return description.charAt(0).toUpperCase() + description.slice(1);
}

export function formatOutlookTimeOnly(iso: string, language: Language): string {
  const date = new Date(iso);
  return new Intl.DateTimeFormat(language === 'BM' ? 'ms-MY' : 'en-MY', {
    timeZone: 'Asia/Kuala_Lumpur',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export interface LaterOutlookRow {
  /** e.g. "+3 hr" — relative to planned departure */
  hoursAfterLabel: string;
  /** e.g. "9:00 am" or "Tomorrow, 9:00 am" */
  clockLabel: string;
  temperature: string;
  note: string | null;
}

const KL_TZ = 'Asia/Kuala_Lumpur';

function sameKlDay(a: Date, b: Date): boolean {
  const fmt = (d: Date) =>
    new Intl.DateTimeFormat('en-CA', {
      timeZone: KL_TZ,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(d);
  return fmt(a) === fmt(b);
}

function formatHoursAfterLabel(hours: number, language: Language): string {
  const rounded = Math.max(1, Math.round(hours));
  return getTranslation(language, 'routeWeatherHoursAfter').replace('{hours}', String(rounded));
}

function formatLaterClockLabel(slotTime: Date, departureTime: Date, language: Language): string {
  const locale = language === 'BM' ? 'ms-MY' : 'en-MY';
  const timePart = new Intl.DateTimeFormat(locale, {
    timeZone: KL_TZ,
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(slotTime);

  if (sameKlDay(slotTime, departureTime)) {
    return timePart;
  }

  const now = new Date();
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const todayLabel = language === 'BM' ? 'Hari ini' : 'Today';
  const tomorrowLabel = language === 'BM' ? 'Esok' : 'Tomorrow';

  if (sameKlDay(slotTime, now)) {
    return `${todayLabel}, ${timePart}`;
  }
  if (sameKlDay(slotTime, tomorrow)) {
    return `${tomorrowLabel}, ${timePart}`;
  }

  const dayPart = new Intl.DateTimeFormat(locale, {
    timeZone: KL_TZ,
    weekday: 'short',
  }).format(slotTime);
  return `${dayPart}, ${timePart}`;
}

const LEAVE_WINDOW_MS = 3 * 60 * 60 * 1000;
const LEAVE_WINDOW_HOURS = 3;

export interface LeaveWindowTimelinePoint {
  hoursAfter: number;
  hoursAfterLabel: string;
  clockLabel: string;
  temperatureC: number;
  temperatureLabel: string;
  condition: string;
  pop: number | null;
  isInterpolated: boolean;
  isDeparture: boolean;
  rainLikely: boolean;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function pickEndSlot(
  slots: WeatherHourlySlot[],
  departureTime: Date,
): WeatherHourlySlot | null {
  const departureMs = departureTime.getTime();
  const candidates = slots
    .filter((slot) => !slot.isDepartureWindow)
    .filter((slot) => {
      const delta = new Date(slot.forecastTime).getTime() - departureMs;
      return delta > 5 * 60 * 1000 && delta <= LEAVE_WINDOW_MS + 15 * 60 * 1000;
    })
    .sort((a, b) => new Date(a.forecastTime).getTime() - new Date(b.forecastTime).getTime());

  if (candidates.length > 0) {
    return candidates[candidates.length - 1];
  }

  const future = slots
    .filter((slot) => new Date(slot.forecastTime).getTime() > departureMs)
    .sort((a, b) => new Date(a.forecastTime).getTime() - new Date(b.forecastTime).getTime());
  return future[0] ?? null;
}

/** Four-point timeline: leave + interpolated +1h/+2h + up to +3h (real forecast when available). */
export function buildLeaveWindowTimeline(
  weather: DestinationWeather,
  language: Language,
  departureTime: Date,
): LeaveWindowTimelinePoint[] {
  const t = (key: TranslationKey) => getTranslation(language, key);
  const leaveLabel = t('routeWeatherLeaveTime');
  const approxSuffix = t('routeWeatherApprox');

  const departureSlot = weather.hourlyOutlook.find((s) => s.isDepartureWindow);
  const startTemp = departureSlot?.temperatureC ?? weather.temperatureC;
  const startCondition = simplifyWeatherCondition(
    departureSlot?.weatherDescription ?? weather.weatherDescription ?? weather.weatherMain,
    language,
  );
  const startPop = departureSlot?.precipitationProbabilityPercent ?? weather.precipitationProbabilityPercent ?? null;

  const endSlot = pickEndSlot(weather.hourlyOutlook, departureTime);
  const endTemp = endSlot?.temperatureC ?? startTemp;
  const endCondition = simplifyWeatherCondition(
    endSlot?.weatherDescription ?? weather.weatherDescription ?? weather.weatherMain,
    language,
  );
  const endPop = endSlot?.precipitationProbabilityPercent ?? startPop;

  const hourOffsets = [0, 1, 2, 3];
  return hourOffsets.map((hoursAfter) => {
    const ratio = hoursAfter / LEAVE_WINDOW_HOURS;
    const slotTime = new Date(departureTime.getTime() + hoursAfter * 60 * 60 * 1000);
    const isDeparture = hoursAfter === 0;
    const isInterpolated = !isDeparture && hoursAfter < LEAVE_WINDOW_HOURS && Boolean(endSlot) && hoursAfter < 3;

    let temperatureC: number;
    let condition: string;
    let pop: number | null;

    if (isDeparture) {
      temperatureC = startTemp;
      condition = startCondition;
      pop = startPop;
    } else if (hoursAfter === LEAVE_WINDOW_HOURS && endSlot) {
      temperatureC = endSlot.temperatureC;
      condition = simplifyWeatherCondition(endSlot.weatherDescription, language);
      pop = endSlot.precipitationProbabilityPercent ?? null;
    } else {
      temperatureC = Math.round(lerp(startTemp, endTemp, ratio) * 10) / 10;
      condition = ratio >= 0.5 ? endCondition : startCondition;
      pop =
        startPop != null && endPop != null
          ? Math.round(lerp(startPop, endPop, ratio))
          : startPop ?? endPop;
    }

    const hoursAfterLabel =
      hoursAfter === 0
        ? leaveLabel
        : formatHoursAfterLabel(hoursAfter, language);

    const clockLabel = formatLaterClockLabel(slotTime, departureTime, language);
    const rainLikely = pop != null && pop >= 40;

    return {
      hoursAfter,
      hoursAfterLabel: isInterpolated ? `${hoursAfterLabel} ${approxSuffix}` : hoursAfterLabel,
      clockLabel,
      temperatureC,
      temperatureLabel: `${temperatureC}°C`,
      condition,
      pop,
      isInterpolated: isInterpolated && hoursAfter < LEAVE_WINDOW_HOURS,
      isDeparture,
      rainLikely,
    };
  });
}

export function buildWeatherChangeSummary(
  timeline: LeaveWindowTimelinePoint[],
  language: Language,
): string {
  const t = (key: TranslationKey) => getTranslation(language, key);
  if (timeline.length < 2) {
    return t('routeWeatherChangeLittle');
  }

  const start = timeline[0];
  const end = timeline[timeline.length - 1];
  const parts: string[] = [];

  const tempDelta = end.temperatureC - start.temperatureC;
  if (tempDelta >= 1.5) {
    parts.push(t('routeWeatherChangeWarmer'));
  } else if (tempDelta <= -1.5) {
    parts.push(t('routeWeatherChangeCooler'));
  } else {
    parts.push(t('routeWeatherChangeTempStable'));
  }

  if (end.condition.toLowerCase() !== start.condition.toLowerCase()) {
    parts.push(t('routeWeatherChangeConditionShift'));
  } else {
    parts.push(t('routeWeatherChangeLittle'));
  }

  if (timeline.some((p) => p.rainLikely)) {
    parts.push(t('routeWeatherRainPossibleShort'));
  }

  return parts.slice(0, 3).join(' · ');
}

/** Forecast rows within 3 hours after planned departure (leave-time card shows "now"). */
export function formatLeaveWindowOutlookRows(
  slots: WeatherHourlySlot[],
  language: Language,
  departureCondition: string,
  departureTime: Date,
): LaterOutlookRow[] {
  const t = (key: TranslationKey) => getTranslation(language, key);
  const normalizedDeparture = departureCondition.trim().toLowerCase();
  const departureMs = departureTime.getTime();

  return slots
    .filter((slot) => {
      if (slot.isDepartureWindow) return false;
      const slotMs = new Date(slot.forecastTime).getTime();
      const deltaMs = slotMs - departureMs;
      return deltaMs > 5 * 60 * 1000 && deltaMs <= LEAVE_WINDOW_MS + 15 * 60 * 1000;
    })
    .sort((a, b) => new Date(a.forecastTime).getTime() - new Date(b.forecastTime).getTime())
    .map((slot) => {
      const slotTime = new Date(slot.forecastTime);
      const hoursAfter = (slotTime.getTime() - departureMs) / (60 * 60 * 1000);
      const condition = simplifyWeatherCondition(slot.weatherDescription, language);
      const pop = slot.precipitationProbabilityPercent;
      const conditionDiffers = condition.toLowerCase() !== normalizedDeparture;

      let note: string | null = null;
      if (pop != null && pop >= 40) {
        note = t('routeWeatherRainPossibleShort');
      } else if (conditionDiffers && condition) {
        note = condition;
      }

      return {
        hoursAfterLabel: formatHoursAfterLabel(hoursAfter, language),
        clockLabel: formatLaterClockLabel(slotTime, departureTime, language),
        temperature: `${slot.temperatureC}°C`,
        note,
      };
    });
}

/** @deprecated Use formatLeaveWindowOutlookRows */
export const formatLaterOutlookRows = formatLeaveWindowOutlookRows;

export function formatHourlyOutlookLabel(iso: string, language: Language): string {
  const date = new Date(iso);
  const now = new Date();
  const locale = language === 'BM' ? 'ms-MY' : 'en-MY';
  const timePart = new Intl.DateTimeFormat(locale, {
    timeZone: 'Asia/Kuala_Lumpur',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);

  const todayLabel = language === 'BM' ? 'Hari ini' : 'Today';
  const tomorrowLabel = language === 'BM' ? 'Esok' : 'Tomorrow';

  const sameDay = (a: Date, b: Date) =>
    new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kuala_Lumpur', year: 'numeric', month: '2-digit', day: '2-digit' })
      .format(a) ===
    new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kuala_Lumpur', year: 'numeric', month: '2-digit', day: '2-digit' })
      .format(b);

  if (sameDay(date, now)) return `${todayLabel} ${timePart}`;
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  if (sameDay(date, tomorrow)) return `${tomorrowLabel} ${timePart}`;
  const dayPart = new Intl.DateTimeFormat(locale, {
    timeZone: 'Asia/Kuala_Lumpur',
    weekday: 'short',
  }).format(date);
  return `${dayPart} ${timePart}`;
}

export function formatHourlyOutlookRows(
  slots: WeatherHourlySlot[],
  language: Language,
): Array<{ timeLabel: string; summary: string; isDeparture: boolean }> {
  return slots.map((slot) => {
    const condition = translateWeatherDescription(slot.weatherDescription, language);
    const pop = slot.precipitationProbabilityPercent;
    const rainHint =
      pop != null && pop >= 40
        ? language === 'BM'
          ? ` · ${pop}% hujan`
          : ` · ${pop}% rain`
        : '';
    return {
      timeLabel: formatHourlyOutlookLabel(slot.forecastTime, language),
      summary: `${slot.temperatureC}°C · ${condition}${rainHint}`,
      isDeparture: slot.isDepartureWindow,
    };
  });
}

export function formatForecastClock(iso: string, language: Language): string {
  const date = new Date(iso);
  return new Intl.DateTimeFormat(language === 'BM' ? 'ms-MY' : 'en-MY', {
    timeZone: 'Asia/Kuala_Lumpur',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export function shouldShowWeatherRiskBadge(weather: DestinationWeather): boolean {
  if (weather.riskLevel === 'clear' || weather.riskLevel === 'unavailable') return false;
  const desc = `${weather.weatherMain} ${weather.weatherDescription}`.toLowerCase();
  if (weather.riskLevel === 'rain' && /rain|drizzle|shower/.test(desc)) return false;
  if (weather.riskLevel === 'storm' && /storm|thunder/.test(desc)) return false;
  if (weather.riskLevel === 'hot' && /hot|clear/.test(desc)) return false;
  return true;
}

export function weatherRiskBadgeLabel(
  weather: DestinationWeather,
  t: (key: TranslationKey) => string,
): string {
  const keys: Record<DestinationWeather['riskLevel'], TranslationKey | ''> = {
    rain: 'routeWeatherRiskRain',
    hot: 'routeWeatherRiskHot',
    storm: 'routeWeatherRiskStorm',
    clear: 'routeWeatherRiskComfort',
    unavailable: '',
  };
  const key = keys[weather.riskLevel];
  return key ? t(key) : '';
}

export interface RainInsight {
  primary: string;
  secondary: string | null;
  showColumn: boolean;
}

export function buildRainInsight(
  weather: DestinationWeather,
  language: Language,
): RainInsight {
  const t = (key: TranslationKey) => getTranslation(language, key);
  const pop = weather.peakPopPercent ?? weather.precipitationProbabilityPercent ?? 0;

  if (weather.rainPeriodStart && weather.rainPeriodEnd) {
    const start = formatForecastClock(weather.rainPeriodStart, language);
    const end = formatForecastClock(weather.rainPeriodEnd, language);
    const hours = weather.rainWindowHours ?? 3;
    return {
      primary: t('routeWeatherRainWhen')
        .replace('{start}', start)
        .replace('{end}', end),
      secondary:
        hours > 3
          ? t('routeWeatherRainDurationHours').replace('{hours}', String(hours))
          : t('routeWeatherRainPopNote').replace('{pop}', String(pop)),
      showColumn: true,
    };
  }

  if (weather.rainMm > 0) {
    return {
      primary: t('routeWeatherRainAmount').replace('{mm}', weather.rainMm.toFixed(1)),
      secondary:
        pop >= 40 ? t('routeWeatherRainPopNote').replace('{pop}', String(pop)) : null,
      showColumn: true,
    };
  }

  if (pop >= 70) {
    return {
      primary: t('routeWeatherRainLikely'),
      secondary: t('routeWeatherRainPopNote').replace('{pop}', String(pop)),
      showColumn: true,
    };
  }

  if (pop >= 40) {
    return {
      primary: t('routeWeatherRainPossible'),
      secondary: t('routeWeatherRainPopNote').replace('{pop}', String(pop)),
      showColumn: true,
    };
  }

  if (weather.riskLevel === 'rain' || weather.riskLevel === 'storm') {
    return {
      primary: t('routeWeatherRainPossible'),
      secondary: null,
      showColumn: true,
    };
  }

  return { primary: '', secondary: null, showColumn: false };
}

export function primarySeniorWeatherTip(
  weather: DestinationWeather,
  language: Language,
): string {
  const t = (key: TranslationKey) => getTranslation(language, key);

  if (weather.riskLevel === 'rain' && weather.rainPeriodStart && weather.rainPeriodEnd) {
    const start = formatForecastClock(weather.rainPeriodStart, language);
    const end = formatForecastClock(weather.rainPeriodEnd, language);
    return t('routeWeatherSeniorRainWindow')
      .replace('{start}', start)
      .replace('{end}', end);
  }

  const tipKeys: Record<DestinationWeather['riskLevel'], [TranslationKey, TranslationKey]> = {
    storm: ['routeWeatherSeniorStorm1', 'routeWeatherSeniorStorm2'],
    rain: ['routeWeatherSeniorRain1', 'routeWeatherSeniorRain2'],
    hot: ['routeWeatherSeniorHot1', 'routeWeatherSeniorHot2'],
    clear: ['routeWeatherSeniorClear1', 'routeWeatherSeniorClear2'],
    unavailable: ['routeWeatherSeniorUnavailable', 'routeWeatherSeniorUnavailable'],
  };
  return t(tipKeys[weather.riskLevel][0]);
}
