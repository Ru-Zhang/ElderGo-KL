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

/**
 * Three-column grid layout for station opening hours and last train times:
 *   col 1 = field label (OPEN / CLOSE / TO X)
 *   col 2 = time
 *   col 3 = condition (e.g. "(Mon - Sat)")
 *
 * All rows live in a single grid so labels with different lengths still
 * keep the time and condition columns vertically aligned. The toggle row
 * uses gridColumn: 1 / -1 to span the full width without breaking the
 * column tracks above and below it.
 */
export function HoursDisplay({ parsed, baseFontSize, t, language, isExpanded, onToggle }: HoursDisplayProps) {
  const valueSize = `${16 * baseFontSize}px`;
  const conditionSize = `${13 * baseFontSize}px`;
  const labelSize = `${11 * baseFontSize}px`;

  const headSections: Array<{ key: string; label: string; entries: ConditionalTime[] }> = [];
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

  const renderRows = (section: { key: string; label: string; entries: ConditionalTime[] }) =>
    section.entries.map((entry, idx) => (
      <React.Fragment key={`${section.key}-${idx}`}>
        <span
          className="text-eldergo-muted font-semibold uppercase tracking-wide whitespace-nowrap self-baseline"
          style={{
            fontSize: labelSize,
            letterSpacing: '0.06em',
            visibility: idx === 0 ? 'visible' : 'hidden',
          }}
        >
          {section.label}
        </span>
        <span
          className="text-eldergo-navy font-bold whitespace-nowrap self-baseline"
          style={{ fontSize: valueSize }}
        >
          {entry.time}
        </span>
        <span
          className="text-eldergo-muted whitespace-nowrap self-baseline"
          style={{ fontSize: conditionSize }}
        >
          {entry.condition ? `(${translateHourCondition(entry.condition, language)})` : ''}
        </span>
      </React.Fragment>
    ));

  return (
    <div
      className="grid"
      style={{
        gridTemplateColumns: 'max-content max-content 1fr',
        rowGap: `${8 * baseFontSize}px`,
        columnGap: `${20 * baseFontSize}px`,
      }}
    >
      {headSections.map((section) => (
        <React.Fragment key={section.key}>{renderRows(section)}</React.Fragment>
      ))}

      {parsed.lastTrains.length > 0 && (
        <button
          type="button"
          onClick={onToggle}
          className="self-start inline-flex items-center gap-1.5 text-eldergo-blue font-semibold"
          style={{
            fontSize: `${14 * baseFontSize}px`,
            gridColumn: '1 / -1',
            marginTop: `${4 * baseFontSize}px`,
            marginBottom: `${2 * baseFontSize}px`,
          }}
        >
          <ChevronDown
            size={16 * baseFontSize}
            strokeWidth={2.4}
            className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
          {isExpanded ? t('hoursHideLastTrains') : t('hoursShowLastTrains')}
        </button>
      )}

      {isExpanded &&
        parsed.lastTrains.map((dest, idx) => (
          <React.Fragment key={`lt-${dest.to}-${idx}`}>
            {renderRows({
              key: `lt-${idx}`,
              label: `${t('hoursLastTrainTo')} ${dest.to}`,
              entries: dest.values,
            })}
          </React.Fragment>
        ))}
    </div>
  );
}
