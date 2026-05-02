import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import * as Switch from '@radix-ui/react-switch';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';

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

        <div className="space-y-6 mb-10">
          <div className="flex items-center justify-between p-6 bg-eldergo-bg rounded-xl border-2 border-eldergo-border">
            <span className="text-[20px] font-medium text-eldergo-navy pr-4 flex-1 leading-tight">
              {t('accessibilityFirst')}
            </span>
            <Switch.Root
              className="w-16 h-8 min-w-16 flex-shrink-0 bg-gray-300 rounded-full relative data-[state=checked]:bg-eldergo-green transition-colors"
              checked={localPreferences.accessibilityFirst}
              onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, accessibilityFirst: checked })}
            >
              <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
            </Switch.Root>
          </div>

          <div className="flex items-center justify-between p-6 bg-eldergo-bg rounded-xl border-2 border-eldergo-border">
            <span className="text-[20px] font-medium text-eldergo-navy pr-4 flex-1 leading-tight">
              {t('leastWalk')}
            </span>
            <Switch.Root
              className="w-16 h-8 min-w-16 flex-shrink-0 bg-gray-300 rounded-full relative data-[state=checked]:bg-eldergo-green transition-colors"
              checked={localPreferences.leastWalk}
              onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, leastWalk: checked })}
            >
              <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
            </Switch.Root>
          </div>

          <div className="flex items-center justify-between p-6 bg-eldergo-bg rounded-xl border-2 border-eldergo-border">
            <span className="text-[20px] font-medium text-eldergo-navy pr-4 flex-1 leading-tight">
              {t('fewestTransfers')}
            </span>
            <Switch.Root
              className="w-16 h-8 min-w-16 flex-shrink-0 bg-gray-300 rounded-full relative data-[state=checked]:bg-eldergo-green transition-colors"
              checked={localPreferences.fewestTransfers}
              onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, fewestTransfers: checked })}
            >
              <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
            </Switch.Root>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark text-white text-[22px] font-semibold py-5 rounded-xl transition-colors min-h-[64px]"
        >
          {t('save')}
        </button>
        {showSavedHint && (
          <div className="mt-4 rounded-lg bg-eldergo-green/15 text-eldergo-green px-4 py-3 text-[16px] font-medium">
            {t('preferenceSavedWeakHint')}
          </div>
        )}
      </div>
    </div>
  );
}
