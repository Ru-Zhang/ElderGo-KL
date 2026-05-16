import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';
import PreferencePriorityList from '../preferences/PreferencePriorityList';
import PreferenceFeedbackBanner from '../preferences/PreferenceFeedbackBanner';

interface PreferencesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function PreferencesModal({ isOpen, onClose }: PreferencesModalProps) {
  const { language, fontSize, preferences, updatePreferences, setOnboardingCompleted } =
    useAppContext();
  const [localPreferences, setLocalPreferences] = useState(preferences);
  const [showSavedHint, setShowSavedHint] = useState(false);
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  useEffect(() => {
    if (isOpen) {
      setLocalPreferences(preferences);
      setShowSavedHint(false);
    }
  }, [isOpen, preferences]);

  const handleSave = () => {
    updatePreferences(localPreferences);
    setOnboardingCompleted(true);
    setShowSavedHint(true);
    window.setTimeout(() => {
      setShowSavedHint(false);
      onClose();
    }, 1800);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center sm:items-center">
      <div className="absolute inset-0 bg-black/55" onClick={onClose} />
      <div
        className="relative flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:rounded-2xl"
        style={{ fontFamily: 'Poppins' }}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 z-20 rounded-full p-2 text-eldergo-navy hover:bg-eldergo-bg"
          aria-label="Close"
        >
          <X size={24} strokeWidth={2.5} />
        </button>

        <div className="overflow-y-auto px-4 pb-3 pt-10 sm:px-6">
          <h2
            className="pr-10 font-bold text-eldergo-navy"
            style={{ fontSize: `${20 * baseFontSize}px` }}
          >
            {t('travelPreferences')}
          </h2>
          <p
            className="mt-1.5 text-eldergo-muted leading-snug"
            style={{ fontSize: `${13 * baseFontSize}px` }}
          >
            {t('priorityOrderHint')}
          </p>

          <div className="mt-4">
            <PreferencePriorityList
              preferences={localPreferences}
              onChange={setLocalPreferences}
              baseFontSize={baseFontSize}
              t={t}
            />
          </div>
        </div>

        <div className="border-t border-eldergo-border px-4 py-3 sm:px-6">
          {showSavedHint ? (
            <div className="mb-2">
              <PreferenceFeedbackBanner
                compact
                variant="saved"
                title={t('preferencesSaved')}
                baseFontSize={baseFontSize}
              />
            </div>
          ) : null}
          <button
            type="button"
            onClick={handleSave}
            className="w-full min-h-[50px] rounded-xl bg-eldergo-warning font-semibold text-white"
            style={{ fontSize: `${17 * baseFontSize}px` }}
          >
            {t('save')}
          </button>
        </div>
      </div>
    </div>
  );
}
