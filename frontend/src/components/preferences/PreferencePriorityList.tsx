import * as Switch from '@radix-ui/react-switch';
import { ArrowDown, ArrowUp } from 'lucide-react';
import type { PreferenceFactor, TravelPreferences } from '../../types/preferences';

interface PreferencePriorityListProps {
  preferences: TravelPreferences;
  onChange: (prefs: TravelPreferences) => void;
  baseFontSize: number;
  t: (key: string) => string;
}

function preferenceLabelKey(factor: PreferenceFactor): string {
  if (factor === 'accessibility') return 'accessibilityFirst';
  if (factor === 'walk') return 'leastWalk';
  return 'fewestTransfers';
}

export default function PreferencePriorityList({
  preferences,
  onChange,
  baseFontSize,
  t,
}: PreferencePriorityListProps) {
  const isEnabled = (factor: PreferenceFactor) => {
    if (factor === 'accessibility') return preferences.accessibilityFirst;
    if (factor === 'walk') return preferences.leastWalk;
    return preferences.fewestTransfers;
  };

  const setEnabled = (factor: PreferenceFactor, checked: boolean) => {
    if (factor === 'accessibility') {
      onChange({ ...preferences, accessibilityFirst: checked });
    } else if (factor === 'walk') {
      onChange({ ...preferences, leastWalk: checked });
    } else {
      onChange({ ...preferences, fewestTransfers: checked });
    }
  };

  const swapAt = (upperIndex: number) => {
    if (upperIndex < 0 || upperIndex >= preferences.priorityOrder.length - 1) return;
    const nextOrder = [...preferences.priorityOrder];
    [nextOrder[upperIndex], nextOrder[upperIndex + 1]] = [
      nextOrder[upperIndex + 1],
      nextOrder[upperIndex],
    ];
    onChange({ ...preferences, priorityOrder: nextOrder });
  };

  const btnSize = Math.round(36 * baseFontSize);
  const iconSize = Math.round(18 * baseFontSize);

  return (
    <ul className="space-y-2.5">
      {preferences.priorityOrder.map((factor, index) => (
        <li
          key={factor}
          className="flex items-center gap-2.5 rounded-xl border border-eldergo-border bg-white/95 px-3 py-3 shadow-sm sm:gap-3 sm:px-4"
        >
          <span
            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-eldergo-blue text-sm font-bold text-white"
            style={{ fontSize: `${15 * baseFontSize}px` }}
            aria-hidden
          >
            {index + 1}
          </span>

          <span
            className="min-w-0 flex-1 font-semibold leading-snug text-eldergo-navy"
            style={{ fontSize: `${16 * baseFontSize}px` }}
          >
            {t(preferenceLabelKey(factor))}
          </span>

          <div className="flex flex-shrink-0 gap-1">
            <button
              type="button"
              onClick={() => index > 0 && swapAt(index - 1)}
              disabled={index === 0}
              className="flex items-center justify-center rounded-lg border border-eldergo-border bg-eldergo-bg/80 text-eldergo-navy disabled:opacity-30"
              style={{ width: btnSize, height: btnSize }}
              aria-label={`${t('priorityMoveUp')}: ${t(preferenceLabelKey(factor))}`}
            >
              <ArrowUp size={iconSize} strokeWidth={2.5} />
            </button>
            <button
              type="button"
              onClick={() => index < preferences.priorityOrder.length - 1 && swapAt(index)}
              disabled={index === preferences.priorityOrder.length - 1}
              className="flex items-center justify-center rounded-lg border border-eldergo-border bg-eldergo-bg/80 text-eldergo-navy disabled:opacity-30"
              style={{ width: btnSize, height: btnSize }}
              aria-label={`${t('priorityMoveDown')}: ${t(preferenceLabelKey(factor))}`}
            >
              <ArrowDown size={iconSize} strokeWidth={2.5} />
            </button>
          </div>

          <Switch.Root
            className="relative h-8 w-[3.5rem] min-w-[3.5rem] flex-shrink-0 rounded-full bg-gray-300 data-[state=checked]:bg-eldergo-green"
            checked={isEnabled(factor)}
            onCheckedChange={(checked) => setEnabled(factor, checked)}
          >
            <Switch.Thumb className="block h-7 w-7 translate-x-0.5 rounded-full bg-white shadow transition-transform data-[state=checked]:translate-x-[1.65rem]" />
          </Switch.Root>
        </li>
      ))}
    </ul>
  );
}
