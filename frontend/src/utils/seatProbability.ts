import seatByDateAndCodeJson from '../data/seatByDateAndCode.json';
import stationNameToCodeJson from '../data/stationNameToCode.json';
import seatProbabilityMetaJson from '../data/seatProbabilityMeta.json';
import { cleanStationQuery } from './stationName';

const stationNameToCode = stationNameToCodeJson as Record<string, string>;
const seatByDateAndCode = seatByDateAndCodeJson as Record<string, number>;
const seatMeta = seatProbabilityMetaJson as {
  dateMin: string;
  dateMax: string;
};

export const SEAT_PROBABILITY_DATE_MIN = seatMeta.dateMin;
export const SEAT_PROBABILITY_DATE_MAX = seatMeta.dateMax;

export type SeatAvailabilityLevel = 'relaxed' | 'moderate' | 'crowded';

export const SEAT_LEVEL_THRESHOLDS = { crowdedMax: 35, relaxedMin: 65 } as const;

export function getSeatAvailabilityLevel(percent: number): SeatAvailabilityLevel {
  if (percent < SEAT_LEVEL_THRESHOLDS.crowdedMax) return 'crowded';
  if (percent >= SEAT_LEVEL_THRESHOLDS.relaxedMin) return 'relaxed';
  return 'moderate';
}

function canonicalStationKey(name: string): string {
  return name.replace(/\s+/g, ' ').trim().toUpperCase();
}

function stationKeyVariants(name: string): string[] {
  const keys = new Set<string>();
  const canonical = canonicalStationKey(name);
  if (!canonical) return [];
  keys.add(canonical);
  if (canonical.includes(' - ')) {
    const head = canonical.split(' - ')[0].trim();
    if (head) keys.add(head);
  }
  return [...keys];
}

function resolveStopCode(labels: (string | null | undefined)[]): string | null {
  for (const label of labels) {
    if (!label) continue;
    const candidates = [
      ...stationKeyVariants(label),
      ...stationKeyVariants(cleanStationQuery(label)),
    ];
    for (const key of candidates) {
      const code = stationNameToCode[key];
      if (code) return code;
    }
  }
  return null;
}

/** Today if inside CSV range; otherwise null (no seat hint shown). */
export function getTravelDateForSeatLookup(): string | null {
  const today = new Date().toISOString().slice(0, 10);
  if (today >= SEAT_PROBABILITY_DATE_MIN && today <= SEAT_PROBABILITY_DATE_MAX) {
    return today;
  }
  return null;
}

export function getSeatProbabilityPercent(
  labels: (string | null | undefined)[],
  date: string | null,
): number | null {
  if (!date) return null;
  const code = resolveStopCode(labels);
  if (!code) return null;
  const value = seatByDateAndCode[`${date}|${code}`];
  return typeof value === 'number' ? value : null;
}

export type SeatLookupStep = {
  step_type: 'walking' | 'transit' | 'arrival';
  from_station?: string | null;
  to_station?: string | null;
  stationForPopup?: string | null;
};

export function getSeatProbabilityForRouteStep(
  step: SeatLookupStep,
  stationDetails: Record<string, { name?: string } | null | undefined>,
  date: string | null,
): number | null {
  const popupDetail = step.stationForPopup ? stationDetails[step.stationForPopup] : undefined;

  if (step.step_type === 'transit') {
    return getSeatProbabilityPercent(
      [step.from_station, popupDetail?.name, step.stationForPopup, step.from_station && cleanStationQuery(step.from_station)],
      date,
    );
  }

  if (step.step_type === 'walking' && step.stationForPopup) {
    return getSeatProbabilityPercent(
      [step.stationForPopup, popupDetail?.name, cleanStationQuery(step.stationForPopup)],
      date,
    );
  }

  return null;
}
