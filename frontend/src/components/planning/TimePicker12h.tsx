import { ChangeEvent, type ReactNode } from 'react';
import {
  formatTimeLocalDisplay,
  maxTimeLocalForDate,
  minTimeLocalForDate,
} from '../../utils/departureTime';

type Period = 'AM' | 'PM';

const MINUTE_STEP = 5;
const MINUTES = Array.from({ length: 60 / MINUTE_STEP }, (_, i) => i * MINUTE_STEP);
const HOURS = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] as const;

function parseTime24(time24: string): { hour12: number; minute: number; period: Period } {
  const [hourStr, minuteStr] = time24.split(':');
  const hour24 = Number(hourStr);
  const minute = Number(minuteStr);
  const period: Period = hour24 >= 12 ? 'PM' : 'AM';
  let hour12 = hour24 % 12;
  if (hour12 === 0) hour12 = 12;
  return { hour12, minute, period };
}

function snapMinute(minute: number): number {
  const snapped = Math.round(minute / MINUTE_STEP) * MINUTE_STEP;
  return Math.min(55, Math.max(0, snapped));
}

function toTime24(hour12: number, minute: number, period: Period): string {
  let hour24 = hour12 % 12;
  if (period === 'PM') hour24 += 12;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(hour24)}:${pad(snapMinute(minute))}`;
}

function timeToMinutes(time24: string): number {
  const [h, m] = time24.split(':').map(Number);
  return h * 60 + m;
}

function clampTimeToRange(time24: string, min: string, max: string): string {
  const minutes = timeToMinutes(time24);
  const minMinutes = timeToMinutes(min);
  const maxMinutes = timeToMinutes(max);
  if (minutes < minMinutes) return min;
  if (minutes > maxMinutes) return max;
  return time24;
}

function isTimeInRange(time24: string, min: string, max: string): boolean {
  const minutes = timeToMinutes(time24);
  return minutes >= timeToMinutes(min) && minutes <= timeToMinutes(max);
}

function availableMinutesFor(
  hour12: number,
  period: Period,
  min: string,
  max: string,
): number[] {
  return MINUTES.filter((minute) => isTimeInRange(toTime24(hour12, minute, period), min, max));
}

function availableHoursFor(period: Period, min: string, max: string): number[] {
  return HOURS.filter((hour12) => availableMinutesFor(hour12, period, min, max).length > 0);
}

function PeriodToggle({
  period,
  onChange,
  label,
  baseFontSize,
}: {
  period: Period;
  onChange: (next: Period) => void;
  label: string;
  baseFontSize: number;
}) {
  const base =
    'h-11 min-w-[2.75rem] flex-1 px-2 font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-eldergo-blue/40';
  const active = 'bg-eldergo-blue text-white';
  const inactive = 'bg-white text-eldergo-navy hover:bg-eldergo-bg';

  return (
    <div
      role="group"
      aria-label={`${label} AM or PM`}
      className="inline-flex h-11 w-[5.75rem] shrink-0 overflow-hidden rounded-lg border-2 border-eldergo-border"
    >
      <button
        type="button"
        aria-pressed={period === 'AM'}
        onClick={() => onChange('AM')}
        className={`${base} ${period === 'AM' ? active : inactive}`}
        style={{ fontSize: `${14 * baseFontSize}px` }}
      >
        AM
      </button>
      <button
        type="button"
        aria-pressed={period === 'PM'}
        onClick={() => onChange('PM')}
        className={`${base} border-l-2 border-eldergo-border ${period === 'PM' ? active : inactive}`}
        style={{ fontSize: `${14 * baseFontSize}px` }}
      >
        PM
      </button>
    </div>
  );
}

export default function TimePicker12h({
  date,
  value,
  onChange,
  language,
  baseFontSize,
  label,
  icon,
}: {
  date: string;
  value: string;
  onChange: (time24: string) => void;
  language: 'EN' | 'BM';
  baseFontSize: number;
  label: string;
  icon: ReactNode;
}) {
  const min = minTimeLocalForDate(date);
  const max = maxTimeLocalForDate(date);
  const clampedValue = clampTimeToRange(value, min, max);
  const { hour12, minute, period } = parseTime24(clampedValue);
  const hourOptions = availableHoursFor(period, min, max);
  const safeHour12 = hourOptions.includes(hour12) ? hour12 : hourOptions[0] ?? 12;
  const minuteOptions = availableMinutesFor(safeHour12, period, min, max);
  const snappedMinute = minuteOptions.includes(snapMinute(minute))
    ? snapMinute(minute)
    : minuteOptions[minuteOptions.length - 1] ?? 0;
  const displayValue = formatTimeLocalDisplay(
    toTime24(safeHour12, snappedMinute, period),
    language,
  );

  const emit = (nextHour12: number, nextMinute: number, nextPeriod: Period) => {
    const hours = availableHoursFor(nextPeriod, min, max);
    const resolvedHour = hours.includes(nextHour12) ? nextHour12 : hours[0] ?? nextHour12;
    const minutes = availableMinutesFor(resolvedHour, nextPeriod, min, max);
    const resolvedMinute = minutes.includes(nextMinute)
      ? nextMinute
      : minutes[minutes.length - 1] ?? 0;
    const next = clampTimeToRange(toTime24(resolvedHour, resolvedMinute, nextPeriod), min, max);
    onChange(next);
  };

  const selectClass =
    'h-11 w-[3.25rem] shrink-0 appearance-none rounded-lg border-2 border-eldergo-border bg-white px-1 text-center font-semibold text-eldergo-navy tabular-nums focus:border-eldergo-blue focus:outline-none focus:ring-2 focus:ring-eldergo-blue/25';

  return (
    <div className="flex w-full min-w-0 flex-col gap-3 rounded-xl border-2 border-eldergo-border bg-white px-3 py-3 sm:px-4">
      <div className="flex min-w-0 items-center gap-3">
        <span className="shrink-0 text-eldergo-blue" aria-hidden>
          {icon}
        </span>
        <span className="min-w-0 flex-1">
          <span
            className="block font-semibold uppercase tracking-wide text-eldergo-muted"
            style={{ fontSize: `${12 * baseFontSize}px` }}
          >
            {label}
          </span>
          <span
            className="mt-0.5 block font-semibold leading-snug text-eldergo-navy tabular-nums"
            style={{ fontSize: `${18 * baseFontSize}px` }}
          >
            {displayValue}
          </span>
        </span>
      </div>

      <div className="flex w-full justify-center">
        <div className="inline-flex max-w-full items-center gap-1.5">
          <select
            aria-label={`${label} hour`}
            value={safeHour12}
            onChange={(e: ChangeEvent<HTMLSelectElement>) =>
              emit(Number(e.target.value), snappedMinute, period)
            }
            className={selectClass}
            style={{ fontSize: `${15 * baseFontSize}px` }}
          >
            {hourOptions.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
          <span className="shrink-0 text-sm font-bold text-eldergo-navy" aria-hidden>
            :
          </span>
          <select
            aria-label={`${label} minute`}
            value={snappedMinute}
            onChange={(e: ChangeEvent<HTMLSelectElement>) =>
              emit(safeHour12, Number(e.target.value), period)
            }
            className={`${selectClass} w-[3.5rem]`}
            style={{ fontSize: `${15 * baseFontSize}px` }}
          >
            {minuteOptions.map((m) => (
              <option key={m} value={m}>
                {String(m).padStart(2, '0')}
              </option>
            ))}
          </select>
          <PeriodToggle
            period={period}
            onChange={(next) => emit(safeHour12, snappedMinute, next)}
            label={label}
            baseFontSize={baseFontSize}
          />
        </div>
      </div>
    </div>
  );
}
