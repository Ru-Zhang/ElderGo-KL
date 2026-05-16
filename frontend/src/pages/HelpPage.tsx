import HelpPageShell from '../components/help/HelpPageShell';
import {
  HelpCallout,
  HelpDivider,
  HelpNavTile,
  HelpPageTitle,
} from '../components/help/HelpPrimitives';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';

interface HelpPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToUseElderGo: () => void;
  onNavigateToTicketGuide: () => void;
  onNavigateToConcessionGuide: () => void;
  onNavigateToPrivacyInfo: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function HelpPage({
  onNavigateToPlanning,
  onNavigateToUseElderGo,
  onNavigateToTicketGuide,
  onNavigateToConcessionGuide,
  onNavigateToPrivacyInfo,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot,
}: HelpPageProps) {
  const { fontSize, language } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const navProps = {
    onChatbotClick: onShowChatbot,
    onStationClick: onNavigateToStation,
    onHelpClick: onNavigateToHelp,
    onPlanningClick: onNavigateToPlanning,
    onPreferenceClick: onNavigateToPreference,
  };

  const handleReset = () => {
    const confirmed = confirm(t('clearCacheConfirm'));
    if (confirmed) {
      const keysBefore = Object.keys(localStorage).filter((key) => key.startsWith('eldergo_'));
      keysBefore.forEach((key) => localStorage.removeItem(key));
      sessionStorage.clear();
      alert(t('clearCacheSuccess'));
      window.location.reload();
    }
  };

  return (
    <HelpPageShell activeTab="help" {...navProps}>
      <HelpPageTitle baseFontSize={baseFontSize}>{t('appIssues')}</HelpPageTitle>

      <button
        type="button"
        onClick={handleReset}
        className="w-full bg-white border-2 border-eldergo-warning text-eldergo-warning font-semibold py-5 rounded-xl hover:bg-eldergo-warning hover:text-white transition-all shadow-md text-center"
        style={{ fontSize: `${20 * baseFontSize}px` }}
      >
        {t('clearCacheReset')}
      </button>

      <HelpCallout baseFontSize={baseFontSize} variant="warning">
        ⚠️ {t('clearCacheWarning')}
      </HelpCallout>

      <HelpDivider />

      <HelpPageTitle baseFontSize={baseFontSize}>{t('helpHeading')}</HelpPageTitle>

      <div className="grid grid-cols-2 gap-4">
        <HelpNavTile
          label={t('useElderGoCard')}
          iconSrc="/icons/help-support.svg"
          onClick={onNavigateToUseElderGo}
          baseFontSize={baseFontSize}
        />
        <HelpNavTile
          label={t('buyTicket')}
          iconSrc="/icons/ticket-guide.svg"
          onClick={onNavigateToTicketGuide}
          baseFontSize={baseFontSize}
          hoverBorderClass="hover:border-eldergo-green"
        />
        <HelpNavTile
          label={t('applyConcession')}
          iconSrc="/icons/concession.svg"
          onClick={onNavigateToConcessionGuide}
          baseFontSize={baseFontSize}
          hoverBorderClass="hover:border-eldergo-warning"
        />
        <HelpNavTile
          label={t('privacyInfo')}
          iconSrc="/icons/privacy.svg"
          onClick={onNavigateToPrivacyInfo}
          baseFontSize={baseFontSize}
          hoverBorderClass="hover:border-eldergo-navy"
        />
      </div>
    </HelpPageShell>
  );
}
