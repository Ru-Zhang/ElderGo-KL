import { Shield, MapPinOff, Archive, Ban } from 'lucide-react';
import HelpPageShell from '../components/help/HelpPageShell';
import { HelpBodyText, HelpContentCard, HelpPageTitle } from '../components/help/HelpPrimitives';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';

interface PrivacyInfoPageProps {
  onNavigateToHelp: () => void;
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function PrivacyInfoPage({
  onNavigateToHelp,
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToPreference,
  onShowChatbot,
}: PrivacyInfoPageProps) {
  const { fontSize, language } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const navProps = {
    onLogoClick: onNavigateToHelp,
    onChatbotClick: onShowChatbot,
    onStationClick: onNavigateToStation,
    onHelpClick: onNavigateToHelp,
    onPlanningClick: onNavigateToPlanning,
    onPreferenceClick: onNavigateToPreference,
  };

  const privacyItems = [
    {
      icon: <MapPinOff size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-green" />,
      bg: 'bg-eldergo-green/20',
      title: t('privacyNoLocationTitle'),
      body: t('privacyNoLocationBody'),
    },
    {
      icon: <Archive size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />,
      bg: 'bg-eldergo-blue/20',
      title: t('privacyNoHistoryTitle'),
      body: t('privacyNoHistoryBody'),
    },
    {
      icon: <Ban size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-warning" />,
      bg: 'bg-eldergo-warning/20',
      title: t('privacyNoAdsTitle'),
      body: t('privacyNoAdsBody'),
    },
  ];

  return (
    <HelpPageShell activeTab="help" {...navProps}>
      <HelpPageTitle
        baseFontSize={baseFontSize}
        icon={
          <div className="w-16 h-16 bg-eldergo-green rounded-full flex items-center justify-center flex-shrink-0">
            <Shield size={36 * baseFontSize} strokeWidth={2.5} className="text-white" />
          </div>
        }
      >
        {t('privacyTitle')}
      </HelpPageTitle>

      <div className="bg-eldergo-blue text-white p-6 rounded-2xl shadow-md border border-eldergo-blue">
        <h3 className="font-bold mb-3" style={{ fontSize: `${24 * baseFontSize}px` }}>
          {t('privacyPromiseTitle')}
        </h3>
        <p className="leading-relaxed" style={{ fontSize: `${20 * baseFontSize}px` }}>
          {t('privacyPromiseBody')}
        </p>
      </div>

      {privacyItems.map((item) => (
        <HelpContentCard key={item.title}>
          <div className="flex items-start gap-4">
            <div
              className={`w-14 h-14 ${item.bg} rounded-full flex items-center justify-center flex-shrink-0`}
            >
              {item.icon}
            </div>
            <div>
              <h4 className="font-semibold text-eldergo-navy mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                {item.title}
              </h4>
              <HelpBodyText baseFontSize={baseFontSize}>{item.body}</HelpBodyText>
            </div>
          </div>
        </HelpContentCard>
      ))}

      <div className="bg-eldergo-bg border-2 border-eldergo-blue p-6 rounded-2xl">
        <p className="text-eldergo-navy leading-relaxed text-center" style={{ fontSize: `${17 * baseFontSize}px` }}>
          {t('privacyFooter')}
        </p>
      </div>
    </HelpPageShell>
  );
}
