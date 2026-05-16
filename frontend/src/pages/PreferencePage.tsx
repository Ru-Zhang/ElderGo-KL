import { useState } from 'react';
import * as Switch from '@radix-ui/react-switch';
import { ArrowDown, ArrowUp, Save } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import type { PreferenceFactor } from '../types/preferences';

interface PreferencePageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function PreferencePage({
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot
}: PreferencePageProps) {
  const { fontSize, language, preferences, updatePreferences } = useAppContext();
  // Keep a local editable copy so users can review/toggle multiple options
  // before committing changes to shared app state.
  const [localPreferences, setLocalPreferences] = useState(preferences);
  const [statusHint, setStatusHint] = useState<'saved' | 'cancelled' | null>(null);

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const handleSave = () => {
    updatePreferences(localPreferences);
    setStatusHint('saved');
    window.setTimeout(() => setStatusHint(null), 3000);
  };

  const handleCancel = () => {
    setLocalPreferences(preferences);
    setStatusHint('cancelled');
    window.setTimeout(() => setStatusHint(null), 3000);
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

  return (
    <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: 'url(/background-elder.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="absolute inset-0 bg-white/38" />
        <div
          className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12'
          }}
        />
      </div>
      <div className="relative z-10">
      <TopBar />

      <main className="pt-20 pb-32 px-6">
        <div className="max-w-2xl mx-auto mt-8">
          <h2 className="font-semibold text-eldergo-navy mb-4" style={{ fontSize: `${24 * baseFontSize}px` }}>
            {t('travelPreferences')}
          </h2>
          <p
            className="text-eldergo-muted mb-8 leading-relaxed"
            style={{ fontSize: `${16 * baseFontSize}px` }}
          >
            {t('travelPreferencesElderNote')}
          </p>

          <div className="mb-8">
            {localPreferences.priorityOrder.map((factor, index) => (
              <div key={factor} className="relative">
                <div className="flex min-h-[118px] items-center gap-3 rounded-xl border-2 border-eldergo-border bg-white px-4 py-5 shadow-md sm:min-h-[138px] sm:gap-5 sm:px-7 sm:py-6">
                  <div
                    className="flex flex-shrink-0 items-center justify-center rounded-full bg-eldergo-blue font-semibold text-white shadow-sm"
                    style={{ width: `${46 * baseFontSize}px`, height: `${46 * baseFontSize}px`, fontSize: `${20 * baseFontSize}px` }}
                  >
                    {index + 1}
                  </div>
                  <span
                    className="flex-1 pr-6 font-semibold text-eldergo-navy leading-tight"
                    style={{ fontSize: `${19 * baseFontSize}px` }}
                  >
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
                  <div className="relative z-10 flex h-16 -my-2 items-center justify-center">
                    <button
                      type="button"
                      onClick={() => swapPriorityAt(index)}
                      className="flex items-center justify-center gap-6 rounded-full border border-eldergo-border bg-white px-8 text-eldergo-navy shadow-md transition-colors hover:bg-eldergo-bg"
                      style={{ height: `${44 * baseFontSize}px` }}
                      aria-label={t('priorityMoveDown' as any)}
                    >
                      <ArrowUp size={22 * baseFontSize} strokeWidth={2.5} />
                      <ArrowDown size={22 * baseFontSize} strokeWidth={2.5} />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSave}
              className="flex-1 flex items-center justify-center gap-3 bg-eldergo-green hover:bg-eldergo-green-dark text-white font-semibold py-5 rounded-xl transition-colors shadow-md min-h-[64px]"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            >
              <Save size={24 * baseFontSize} strokeWidth={2.5} />
              {t('save')}
            </button>
            <button
              onClick={handleCancel}
              className="flex-1 flex items-center justify-center gap-3 bg-white hover:bg-eldergo-bg text-eldergo-muted font-semibold py-5 rounded-xl border-2 border-eldergo-border transition-colors shadow-md min-h-[64px]"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            >
              {t('cancel')}
            </button>
          </div>
          {statusHint && (
            <div
              className="fixed left-4 right-4 bottom-28 z-50 mx-auto max-w-2xl rounded-xl px-5 py-4 text-center font-semibold shadow-lg"
              style={{
                backgroundColor: statusHint === 'saved' ? '#65C25A' : '#1B3A5F',
                color: '#ffffff',
                fontSize: `${17 * baseFontSize}px`,
              }}
              role="status"
            >
              {statusHint === 'saved' ? t('preferenceSavedWeakHint') : t('preferenceCancelledHint')}
            </div>
          )}
        </div>
      </main>

        <BottomNav
          activeTab="preference"
          onChatbotClick={onShowChatbot}
          onStationClick={onNavigateToStation}
          onHelpClick={onNavigateToHelp}
          onPlanningClick={onNavigateToPlanning}
          onPreferenceClick={onNavigateToPreference}
        />
      </div>
    </div>
  );
}
