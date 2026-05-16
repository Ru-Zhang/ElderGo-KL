import { Sparkles } from 'lucide-react';
import type { TranslationKey } from '../../i18n/translations';
import { rankingFactorTranslationKey } from '../../utils/rankingDisplay';

export interface RouteRankingInsightProps {
  primaryFactor?: string | null;
  secondaryFactor?: string | null;
  baseFontSize: number;
  t: (key: TranslationKey) => string;
}

export default function RouteRankingInsight({
  primaryFactor,
  secondaryFactor,
  baseFontSize,
  t,
}: RouteRankingInsightProps) {
  const primaryKey = rankingFactorTranslationKey(primaryFactor, 'primary');
  const secondaryKey = rankingFactorTranslationKey(secondaryFactor, 'secondary');

  if (!primaryKey && !secondaryKey) return null;

  return (
    <div
      className="mt-3 flex flex-col gap-1 rounded-lg bg-eldergo-bg/80 px-3 py-2.5 text-left"
      title={t('routePreferenceDataLead')}
    >
      <p
        className="flex items-center gap-1 text-eldergo-blue"
        style={{ fontSize: `${11 * baseFontSize}px` }}
      >
        <Sparkles
          size={12 * baseFontSize}
          strokeWidth={2.5}
          className="flex-shrink-0"
          aria-hidden
        />
        <span className="font-semibold uppercase tracking-wide">
          {t('routeRankingRecommended')}
        </span>
      </p>
      {primaryKey ? (
        <p
          className="font-semibold leading-snug text-eldergo-navy"
          style={{ fontSize: `${15 * baseFontSize}px` }}
        >
          {t(primaryKey as TranslationKey)}
        </p>
      ) : null}
      {secondaryKey ? (
        <p
          className="leading-snug text-eldergo-muted"
          style={{ fontSize: `${14 * baseFontSize}px` }}
        >
          {t(secondaryKey as TranslationKey)}
        </p>
      ) : null}
    </div>
  );
}
