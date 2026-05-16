import { AlertCircle } from 'lucide-react';
import { PlaceSelection } from '../../types/locations';
import { formatDepartureContextLabel } from '../../utils/departureTime';
import { formatPlaceDisplayName } from '../../utils/placeDisplay';
import type { LanguageCode } from '../../types/settings';
import type { TranslationKey } from '../../i18n/translations';

export type RouteUnavailableVariant = 'no_transit' | 'generic';

interface RouteUnavailableViewProps {
  variant: RouteUnavailableVariant;
  departureTime: string;
  origin: PlaceSelection | null;
  destination: PlaceSelection | null;
  baseFontSize: number;
  language: LanguageCode;
  message?: string | null;
  t: (key: TranslationKey) => string;
  onNavigateToPlanTime: () => void;
  onNavigateToPlanning: () => void;
}

export default function RouteUnavailableView({
  variant,
  departureTime,
  origin,
  destination,
  baseFontSize,
  language,
  message,
  t,
  onNavigateToPlanTime,
  onNavigateToPlanning,
}: RouteUnavailableViewProps) {
  const titleKey: TranslationKey =
    variant === 'no_transit' ? 'routeNoTransitTitle' : 'routeGenericErrorTitle';
  const bodyKey: TranslationKey =
    variant === 'no_transit' ? 'routeNoTransitBody' : 'planTimeUnableToRoute';

  const titleSize = 26 * baseFontSize;
  const bodySize = 18 * baseFontSize;
  const labelSize = 16 * baseFontSize;
  const iconSize = 64 * baseFontSize;
  const customIso = departureTime.includes('T') ? departureTime : undefined;
  const preset = customIso ? 'now' : departureTime;
  const departureTimeLabel = formatDepartureContextLabel(preset, language, customIso);
  const departureLabel = departureTimeLabel
    ? t('planTimeLeavingAt').replace('{time}', departureTimeLabel)
    : '';
  const fromLabel = formatPlaceDisplayName(origin?.displayName);
  const toLabel = formatPlaceDisplayName(destination?.displayName);

  return (
    <div
      className="bg-white/95 rounded-2xl shadow-md border-2 border-eldergo-border p-6 sm:p-8 text-center"
      role="alert"
      aria-live="polite"
    >
      <div
        className="mx-auto mb-5 rounded-full bg-eldergo-warning/15 flex items-center justify-center text-eldergo-warning"
        style={{ width: iconSize + 24, height: iconSize + 24 }}
      >
        <AlertCircle size={iconSize} strokeWidth={2.2} aria-hidden />
      </div>

      <h2
        className="font-semibold text-eldergo-navy mb-3 leading-snug"
        style={{ fontSize: `${titleSize}px` }}
      >
        {t(titleKey)}
      </h2>

      <p
        className="text-eldergo-muted mb-5 leading-relaxed"
        style={{ fontSize: `${bodySize}px` }}
      >
        {variant === 'generic' && message ? message : t(bodyKey)}
      </p>

      {fromLabel && toLabel ? (
        <p
          className="text-eldergo-navy font-medium mb-2"
          style={{ fontSize: `${labelSize}px` }}
        >
          {fromLabel} → {toLabel}
        </p>
      ) : null}

      {departureLabel ? (
        <p className="text-eldergo-muted mb-6" style={{ fontSize: `${labelSize}px` }}>
          {departureLabel}
        </p>
      ) : null}

      <div className="flex flex-col gap-3">
        <button
          type="button"
          onClick={onNavigateToPlanTime}
          className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark text-white font-semibold py-4 rounded-xl transition-colors shadow-md"
          style={{ fontSize: `${bodySize}px` }}
        >
          {t('routeNoTransitChangeTime')}
        </button>
        <button
          type="button"
          onClick={onNavigateToPlanning}
          className="w-full bg-white hover:bg-eldergo-bg text-eldergo-navy font-semibold py-4 rounded-xl transition-colors border-2 border-eldergo-border"
          style={{ fontSize: `${bodySize}px` }}
        >
          {t('routeNoTransitChangePlaces')}
        </button>
      </div>
    </div>
  );
}
