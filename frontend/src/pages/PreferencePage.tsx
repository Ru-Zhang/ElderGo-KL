import { useEffect, useState } from 'react';
import HelpPageShell from '../components/help/HelpPageShell';
import { HelpBodyText, HelpPageTitle } from '../components/help/HelpPrimitives';
import PreferencePriorityList from '../components/preferences/PreferencePriorityList';
import PreferenceFeedbackBanner from '../components/preferences/PreferenceFeedbackBanner';
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
  onShowChatbot,
}: PreferencePageProps) {
  const { fontSize, language, preferences, updatePreferences } = useAppContext();
  const [localPreferences, setLocalPreferences] = useState(preferences);
  const [statusHint, setStatusHint] = useState<'saved' | 'reset' | null>(null);

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  useEffect(() => {
    setLocalPreferences(preferences);
  }, [preferences]);

  useEffect(() => {
    if (!statusHint) return;
    const timer = window.setTimeout(() => setStatusHint(null), 4000);
    return () => window.clearTimeout(timer);
  }, [statusHint]);

  const handleSave = () => {
    updatePreferences(localPreferences);
    setStatusHint('saved');
  };

  const handleReset = () => {
    setLocalPreferences(preferences);
    setStatusHint('reset');
  };

  const navProps = {
    onChatbotClick: onShowChatbot,
    onStationClick: onNavigateToStation,
    onHelpClick: onNavigateToHelp,
    onPlanningClick: onNavigateToPlanning,
    onPreferenceClick: onNavigateToPreference,
  };

  return (
    <HelpPageShell activeTab="preference" {...navProps}>
      <HelpPageTitle baseFontSize={baseFontSize}>{t('travelPreferences')}</HelpPageTitle>

      <HelpBodyText baseFontSize={baseFontSize}>{t('travelPreferencesElderNote')}</HelpBodyText>

      <HelpBodyText baseFontSize={baseFontSize} className="-mt-3 opacity-90">
        {t('priorityOrderHint')}
      </HelpBodyText>

      {statusHint ? (
        <PreferenceFeedbackBanner
          compact
          variant={statusHint}
          title={statusHint === 'saved' ? t('preferencesSaved') : t('preferenceResetHint')}
          baseFontSize={baseFontSize}
        />
      ) : null}

      <PreferencePriorityList
        preferences={localPreferences}
        onChange={setLocalPreferences}
        baseFontSize={baseFontSize}
        t={t}
      />

      <div className="flex gap-2.5">
            <button
          type="button"
              onClick={handleSave}
          className="min-h-[52px] flex-1 rounded-xl bg-eldergo-green font-semibold text-white shadow-sm transition-colors hover:bg-eldergo-green-dark"
          style={{ fontSize: `${17 * baseFontSize}px` }}
            >
              {t('save')}
            </button>
            <button
          type="button"
          onClick={handleReset}
          className="min-h-[52px] flex-1 rounded-xl border border-eldergo-border bg-white font-semibold text-eldergo-navy shadow-sm transition-colors hover:bg-eldergo-bg"
          style={{ fontSize: `${17 * baseFontSize}px` }}
        >
          {t('reset')}
            </button>
      </div>
    </HelpPageShell>
  );
}
