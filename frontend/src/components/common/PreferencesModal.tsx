import { useState, useEffect } from 'react';
import { ArrowDown, ArrowUp, X } from 'lucide-react';
import * as Switch from '@radix-ui/react-switch';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';
import type { PreferenceFactor } from '../../types/preferences';

interface PreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function PreferencesModal({ isOpen, onClose }: PreferencesModalProps) {
  const { language, preferences, updatePreferences, setOnboardingCompleted } = useAppContext();
  // Local copy lets users adjust multiple toggles before one save action.
  const [localPreferences, setLocalPreferences] = useState(preferences);
  const [showSavedHint, setShowSavedHint] = useState(false);
  const t = (key: string) => getTranslation(language, key as any);

  useEffect(() => {
    if (isOpen) {
      // Reset draft values each time modal opens to reflect latest stored prefs.
      setLocalPreferences(preferences);
    }
  }, [isOpen, preferences]);

  const handleSave = () => {
    updatePreferences(localPreferences);
    // Completing this modal marks onboarding preference step as done.
    setOnboardingCompleted(true);
    setShowSavedHint(true);
    window.setTimeout(() => {
      setShowSavedHint(false);
      onClose();
    }, 1200);
  };

  const isPreferenceEnabled = (factor: PreferenceFactor) => {
    if (factor === 'accessibility') return localPreferences.accessibilityFirst;
    if (factor === 'walk') return localPreferences.leastWalk;
    return localPreferences.fewestTransfers;
  };

  const preferenceLabelKey = (factor: PreferenceFactor) => {
    if (factor === 'accessibility') return 'accessibilityFirst';
    if (factor === 'walk') return 'leastWalk';
    return 'fewestTransfers';
  };

  const setPreferenceEnabled = (factor: PreferenceFactor, checked: boolean) => {
    if (factor === 'accessibility') {
      setLocalPreferences({ ...localPreferences, accessibilityFirst: checked });
    } else if (factor === 'walk') {
      setLocalPreferences({ ...localPreferences, leastWalk: checked });
    } else {
      setLocalPreferences({ ...localPreferences, fewestTransfers: checked });
    }
  };

  const swapPriorityAt = (upperIndex: number) => {
    if (upperIndex < 0 || upperIndex >= localPreferences.priorityOrder.length - 1) return;
    const nextOrder = [...localPreferences.priorityOrder];
    [nextOrder[upperIndex], nextOrder[upperIndex + 1]] = [nextOrder[upperIndex + 1], nextOrder[upperIndex]];
    setLocalPreferences({ ...localPreferences, priorityOrder: nextOrder });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 sm:mx-6 p-6 sm:p-8 pt-10" style={{ fontFamily: 'Poppins' }}>
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-eldergo-navy hover:bg-eldergo-bg rounded-full p-2 z-20"
          aria-label="Close preferences modal"
        >
          <X size={28} strokeWidth={2.5} />
        </button>

        <h2 className="text-[26px] sm:text-3xl font-semibold text-eldergo-navy mb-8 pr-14 leading-none whitespace-nowrap">
          {t('travelPreferences')}
        </h2>

        <div className="mb-10">
          {localPreferences.priorityOrder.map((factor, index) => (
            <div key={factor} className="relative">
              <div className="flex min-h-[112px] items-center gap-4 rounded-xl border-2 border-eldergo-border bg-white px-5 py-5 shadow-md sm:min-h-[124px] sm:px-6">
                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-eldergo-blue text-[20px] font-semibold text-white shadow-sm">
                  {index + 1}
                </div>
                <span className="flex-1 pr-4 text-[20px] font-semibold leading-tight text-eldergo-navy">
                  {t(preferenceLabelKey(factor) as any)}
                </span>
                <Switch.Root
                  className="w-16 h-8 min-w-16 flex-shrink-0 bg-gray-300 rounded-full relative data-[state=checked]:bg-eldergo-green transition-colors"
                  checked={isPreferenceEnabled(factor)}
                  onCheckedChange={(checked) => setPreferenceEnabled(factor, checked)}
                >
                  <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
                </Switch.Root>
              </div>
              {index < localPreferences.priorityOrder.length - 1 && (
                <div className="relative z-10 flex h-14 -my-2 items-center justify-center">
                  <button
                    type="button"
                    onClick={() => swapPriorityAt(index)}
                    className="flex h-11 w-32 items-center justify-center gap-6 rounded-full border border-eldergo-border bg-white text-eldergo-navy shadow-md transition-colors hover:bg-eldergo-bg"
                    aria-label={t('priorityMoveDown' as any)}
                  >
                    <ArrowUp size={22} strokeWidth={2.5} />
                    <ArrowDown size={22} strokeWidth={2.5} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={handleSave}
          className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark text-white text-[22px] font-semibold py-5 rounded-xl transition-colors min-h-[64px]"
        >
          {t('save')}
        </button>
        {showSavedHint && (
          <div className="mt-4 rounded-xl bg-eldergo-green px-4 py-3 text-center text-[16px] font-semibold text-white shadow-md">
            {t('preferenceSavedWeakHint')}
          </div>
        )}
      </div>
    </div>
  );
}
