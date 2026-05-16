import { CheckCircle2, RotateCcw } from 'lucide-react';

interface PreferenceFeedbackBannerProps {
  variant: 'saved' | 'reset';
  title: string;
  detail?: string;
  baseFontSize: number;
  compact?: boolean;
}

export default function PreferenceFeedbackBanner({
  variant,
  title,
  detail,
  baseFontSize,
  compact = false,
}: PreferenceFeedbackBannerProps) {
  const isSaved = variant === 'saved';
  const Icon = isSaved ? CheckCircle2 : RotateCcw;

  if (compact) {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`flex items-center gap-2 rounded-lg px-3 py-2.5 ${
          isSaved ? 'bg-eldergo-green/15 text-eldergo-green' : 'bg-eldergo-navy/10 text-eldergo-navy'
        }`}
      >
        <Icon size={20 * baseFontSize} strokeWidth={2.5} aria-hidden className="flex-shrink-0" />
        <p className="font-semibold leading-snug" style={{ fontSize: `${14 * baseFontSize}px` }}>
          {title}
          {detail ? ` — ${detail}` : ''}
        </p>
      </div>
    );
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-start gap-3 rounded-2xl border-2 px-4 py-4 shadow-lg ${
        isSaved
          ? 'border-eldergo-green/40 bg-eldergo-green text-white'
          : 'border-eldergo-navy/20 bg-eldergo-navy text-white'
      }`}
    >
      <Icon
        className="mt-0.5 flex-shrink-0"
        size={28 * baseFontSize}
        strokeWidth={2.5}
        aria-hidden
      />
      <div className="min-w-0 text-left">
        <p className="font-bold leading-snug" style={{ fontSize: `${18 * baseFontSize}px` }}>
          {title}
        </p>
        {detail ? (
          <p
            className={`mt-1 leading-relaxed ${isSaved ? 'text-white/95' : 'text-white/85'}`}
            style={{ fontSize: `${15 * baseFontSize}px` }}
          >
            {detail}
          </p>
        ) : null}
      </div>
    </div>
  );
}
