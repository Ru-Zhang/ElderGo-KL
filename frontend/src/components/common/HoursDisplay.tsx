import * as React from 'react';
import { ChevronDown } from 'lucide-react';
import type { ParsedHours, ConditionalTime } from '../../utils/hoursParser';
import type { Language } from '../../i18n/translations';
import { translateHourCondition } from '../../utils/dataI18n';

interface HoursDisplayProps {
  parsed: ParsedHours;
  baseFontSize: number;
  t: (key: string) => string;
  language: Language;
  isExpanded: boolean;
  onToggle: () => void;
}

interface Section {
  key: string;
  label: string;
  entries: ConditionalTime[];
}

/**
 * Section-stacked layout for station opening hours and last train times.
 *
 * Each field (OPEN / CLOSE / TO X) renders its label on its own row, then
 * a two-column row for the time(s) and the conditional weekday tag.
 * That keeps the time and the "(Mon - Sat)" hint flush-left under the
 * section header — earlier we used a left label column that wasted ~30%
 * of the row width on phones and squeezed the condition into a tiny slice.
 */
export function HoursDisplay({ parsed, baseFontSize, t, language, isExpanded, onToggle }: HoursDisplayProps) {
  const valueSize = `${16 * baseFontSize}px`;
  const conditionSize = `${13 * baseFontSize}px`;
  const labelSize = `${11 * baseFontSize}px`;

  /** Cap gaps so they don't blow up at A++ scale on narrow viewports. */
  const columnGapPx = Math.min(16, 8 + 5 * baseFontSize);
  const rowGapPx = Math.min(10, 4 + 2 * baseFontSize);
  const sectionGapPx = Math.min(20, 10 + 6 * baseFontSize);

  const headSections: Section[] = [];
  if (parsed.open.length > 0) {
    headSections.push({ key: 'open', label: t('hoursOpen'), entries: parsed.open });
  }
  if (parsed.close.length > 0) {
    headSections.push({ key: 'close', label: t('hoursClose'), entries: parsed.close });
  }
  if (parsed.other.length > 0) {
    headSections.push({
      key: 'other',
      label: t('hoursLastTrain'),
      entries: parsed.other.map((line) => ({ time: line, condition: '' })),
    });
  }

  const renderSection = (section: Section) => (
    <div key={section.key} className="w-full min-w-0">
      <div
        className="text-eldergo-muted font-semibold uppercase tracking-wide"
        style={{ fontSize: labelSize, letterSpacing: '0.06em', marginBottom: `${rowGapPx}px` }}
      >
        {section.label}
      </div>
      <div
        className="grid w-full min-w-0"
        style={{
          gridTemplateColumns: 'max-content minmax(0, 1fr)',
          columnGap: `${columnGapPx}px`,
          rowGap: `${rowGapPx}px`,
        }}
      >
        {section.entries.map((entry, idx) => (
          <React.Fragment key={`${section.key}-${idx}`}>
            <span
              className="text-eldergo-navy font-bold whitespace-nowrap tabular-nums self-baseline"
              style={{ fontSize: valueSize }}
            >
              {entry.time}
            </span>
            <span
              className="text-eldergo-muted self-baseline break-words min-w-0"
              style={{ fontSize: conditionSize }}
            >
              {entry.condition ? `(${translateHourCondition(entry.condition, language)})` : ''}
            </span>
          </React.Fragment>
        ))}
      </div>
    </div>
  );

  return (
    <div
      className="flex w-full min-w-0 max-w-full flex-col"
      style={{ gap: `${sectionGapPx}px` }}
    >
      {headSections.map(renderSection)}

      {parsed.lastTrains.length > 0 && (
        <button
          type="button"
          onClick={onToggle}
          className="self-start inline-flex items-center gap-1.5 text-eldergo-blue font-semibold text-left min-w-0"
          style={{
            fontSize: `${14 * baseFontSize}px`,
            marginTop: `-${Math.round(sectionGapPx / 2)}px`,
          }}
        >
          <ChevronDown
            size={16 * baseFontSize}
            strokeWidth={2.4}
            className={`flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
          <span className="min-w-0 break-words">
            {isExpanded ? t('hoursHideLastTrains') : t('hoursShowLastTrains')}
          </span>
        </button>
      )}

      {isExpanded &&
        parsed.lastTrains.map((dest, idx) =>
          renderSection({
            key: `lt-${dest.to}-${idx}`,
            label: `${t('hoursLastTrainTo')} ${dest.to}`,
            entries: dest.values,
          }),
        )}
    </div>
  );
}
