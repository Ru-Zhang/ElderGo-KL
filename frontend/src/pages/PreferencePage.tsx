import { useState } from 'react';
import * as Switch from '@radix-ui/react-switch';
import { Save } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';

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
  const { fontSize, language, preferences, updatePreferences, clearPreferences } = useAppContext();
  const [localPreferences, setLocalPreferences] = useState(preferences);
  const [showSavedHint, setShowSavedHint] = useState(false);

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const handleSave = () => {
    updatePreferences(localPreferences);
    setShowSavedHint(true);
    window.setTimeout(() => setShowSavedHint(false), 2000);
  };

  const handleCancel = () => {
    setLocalPreferences(preferences);
  };

  return (
    <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: 'url(/background-elder.jpg)',
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
          <h2 className="font-semibold text-[#1E3A5F] mb-8" style={{ fontSize: `${24 * baseFontSize}px` }}>
            {t('travelPreferences')}
          </h2>

          <div className="space-y-4 mb-8">
            <div className="flex items-center justify-between p-6 bg-white rounded-xl border-2 border-gray-200 shadow-sm">
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('accessibilityFirst')}
              </span>
              <Switch.Root
                className="w-16 h-8 bg-gray-300 rounded-full relative data-[state=checked]:bg-[#6BBF59] transition-colors"
                checked={localPreferences.accessibilityFirst}
                onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, accessibilityFirst: checked })}
              >
                <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
              </Switch.Root>
            </div>

            <div className="flex items-center justify-between p-6 bg-white rounded-xl border-2 border-gray-200 shadow-sm">
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('leastWalk')}
              </span>
              <Switch.Root
                className="w-16 h-8 bg-gray-300 rounded-full relative data-[state=checked]:bg-[#6BBF59] transition-colors"
                checked={localPreferences.leastWalk}
                onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, leastWalk: checked })}
              >
                <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
              </Switch.Root>
            </div>

            <div className="flex items-center justify-between p-6 bg-white rounded-xl border-2 border-gray-200 shadow-sm">
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('fewestTransfers')}
              </span>
              <Switch.Root
                className="w-16 h-8 bg-gray-300 rounded-full relative data-[state=checked]:bg-[#6BBF59] transition-colors"
                checked={localPreferences.fewestTransfers}
                onCheckedChange={(checked) => setLocalPreferences({ ...localPreferences, fewestTransfers: checked })}
              >
                <Switch.Thumb className="block w-7 h-7 bg-white rounded-full shadow-lg transition-transform translate-x-0.5 data-[state=checked]:translate-x-[34px]" />
              </Switch.Root>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSave}
              className="flex-1 flex items-center justify-center gap-3 bg-[#6BBF59] hover:bg-[#5AAF49] text-white font-semibold py-5 rounded-xl transition-colors shadow-md min-h-[64px]"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            >
              <Save size={24 * baseFontSize} strokeWidth={2.5} />
              {t('save')}
            </button>
            <button
              onClick={handleCancel}
              className="flex-1 flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-600 font-semibold py-5 rounded-xl border-2 border-gray-300 transition-colors shadow-md min-h-[64px]"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            >
              {t('cancel')}
            </button>
          </div>
          {showSavedHint && (
            <div className="mt-4 rounded-lg bg-[#EAF6EA] text-[#2F7A32] px-4 py-3 text-[16px] font-medium">
              {t('preferenceSavedWeakHint')}
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
