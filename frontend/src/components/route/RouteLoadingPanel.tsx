import { useEffect, useState } from 'react';
import { Loader2, Train } from 'lucide-react';
import { PlaceSelection } from '../../types/locations';
import { formatPlaceDisplayName } from '../../utils/placeDisplay';
import type { TranslationKey } from '../../i18n/translations';

interface RouteLoadingPanelProps {
  origin: PlaceSelection | null;
  destination: PlaceSelection | null;
  baseFontSize: number;
  t: (key: TranslationKey) => string;
}

export default function RouteLoadingPanel({
  origin,
  destination,
  baseFontSize,
  t,
}: RouteLoadingPanelProps) {
  const [reduceMotion, setReduceMotion] = useState(false);
  const [showSlowHint, setShowSlowHint] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setShowSlowHint(true), 20_000);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduceMotion(media.matches);
    update();
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  const fromLabel = formatPlaceDisplayName(origin?.displayName) || '—';
  const toLabel = formatPlaceDisplayName(destination?.displayName) || '—';
  const titleSize = 22 * baseFontSize;
  const hintSize = 16 * baseFontSize;
  const summarySize = 18 * baseFontSize;
  const iconRing = 72 * baseFontSize;
  const trainIcon = 36 * baseFontSize;
  const spinnerIcon = 36 * baseFontSize;

  return (
    <div
      className="relative z-10 w-full max-w-md bg-white rounded-2xl shadow-xl border-2 border-eldergo-border flex flex-col items-center justify-center text-center px-6 py-8"
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={t('routeComputing')}
    >
      <div
        className="mb-5 rounded-full bg-eldergo-blue/15 flex items-center justify-center"
        style={{ width: iconRing, height: iconRing }}
      >
        {reduceMotion ? (
          <Train
            className="text-eldergo-blue"
            size={trainIcon}
            strokeWidth={2.5}
            aria-hidden
          />
        ) : (
          <Loader2
            className="text-eldergo-blue animate-spin"
            size={spinnerIcon}
            strokeWidth={2.5}
            aria-hidden
          />
        )}
      </div>

      <h2
        className="font-semibold text-eldergo-navy mb-3 leading-snug"
        style={{ fontSize: `${titleSize}px` }}
      >
        {t('routeComputingTitle')}
      </h2>

      <p
        className="font-semibold text-eldergo-navy mb-4 leading-snug break-words [overflow-wrap:anywhere] max-w-full"
        style={{ fontSize: `${summarySize}px` }}
      >
        <span className="text-eldergo-muted font-medium">{fromLabel}</span>
        <span className="mx-2 text-eldergo-blue" aria-hidden>
          →
        </span>
        <span>{toLabel}</span>
      </p>

      <p
        className="text-eldergo-muted font-medium max-w-sm leading-relaxed"
        style={{ fontSize: `${hintSize}px` }}
      >
        {t('routeComputingHint')}
      </p>
      {showSlowHint && (
        <p
          className="text-eldergo-muted mt-3 max-w-sm leading-relaxed"
          style={{ fontSize: `${hintSize}px` }}
        >
          {t('routeComputingSlowHint')}
        </p>
      )}
    </div>
  );
}
