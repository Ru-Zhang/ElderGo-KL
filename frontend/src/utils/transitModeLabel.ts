import type { Language } from '../i18n/translations';
import { getTranslation, type TranslationKey } from '../i18n/translations';

type TransitLabelKey =
  | 'transitModeBrt'
  | 'transitModeLrt'
  | 'transitModeMrt'
  | 'transitModeBus'
  | 'transitModeTrain'
  | 'transitModeFerry'
  | 'transitModeTransit';

function lineHaystack(transitLine?: string | null, transitHeadsign?: string | null): string {
  return `${transitLine || ''} ${transitHeadsign || ''}`.toUpperCase();
}

/** Map Google vehicle type + line name to KL-specific labels (LRT/MRT/BRT). */
export function resolveTransitModeKey(
  transitLine?: string | null,
  transitVehicleType?: string | null,
  transitHeadsign?: string | null,
): TransitLabelKey {
  const line = lineHaystack(transitLine, transitHeadsign);
  const vehicle = (transitVehicleType || '').toUpperCase();

  if (/BRT|SUNU|SUNWAY/i.test(line)) return 'transitModeBrt';
  if (/MRT|SBK|KAJANG|\bKG\b|PY\d|PUTRAJAYA/i.test(line)) return 'transitModeMrt';
  if (/LRT|KELANA|\bKJ\b|AMPANG|SR|\bAG\b|\bSP\b|\bPH\b/i.test(line)) return 'transitModeLrt';
  if (vehicle === 'BUS') return 'transitModeBus';
  if (vehicle === 'FERRY') return 'transitModeFerry';
  if (vehicle === 'TRAIN' || vehicle === 'HEAVY_RAIL' || vehicle === 'RAIL') return 'transitModeTrain';
  if (vehicle === 'SUBWAY' || vehicle === 'METRO' || vehicle === 'TRAM') return 'transitModeLrt';
  return 'transitModeTransit';
}

export function formatTransitModeLabel(
  language: Language,
  transitLine?: string | null,
  transitVehicleType?: string | null,
  transitHeadsign?: string | null,
): string {
  const key = resolveTransitModeKey(transitLine, transitVehicleType, transitHeadsign);
  return getTranslation(language, key);
}

export function formatTransitStepTitle(
  language: Language,
  fromStation: string,
  toStation: string,
  transitLine?: string | null,
  transitVehicleType?: string | null,
  transitHeadsign?: string | null,
): string {
  const mode = formatTransitModeLabel(language, transitLine, transitVehicleType, transitHeadsign);
  const actionFrom = getTranslation(language, 'routeActionFrom' as TranslationKey);
  const actionTo = getTranslation(language, 'routeActionTo' as TranslationKey);
  return `${mode} ${actionFrom} ${fromStation} ${actionTo} ${toStation}`;
}
