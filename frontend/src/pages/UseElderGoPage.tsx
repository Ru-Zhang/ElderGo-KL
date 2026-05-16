import { MapPin, Sliders, HelpCircle, User, Building2 } from 'lucide-react';
import HelpPageShell from '../components/help/HelpPageShell';
import {
  HelpBodyText,
  HelpCallout,
  HelpContentCard,
  HelpPageTitle,
  HelpPrimaryButton,
  HelpStepCard,
} from '../components/help/HelpPrimitives';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';

interface UseElderGoPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToHelp: () => void;
  onNavigateToStation: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function UseElderGoPage({
  onNavigateToPlanning,
  onNavigateToHelp,
  onNavigateToStation,
  onNavigateToPreference,
  onShowChatbot,
}: UseElderGoPageProps) {
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

  return (
    <HelpPageShell activeTab="help" {...navProps}>
      <HelpPageTitle baseFontSize={baseFontSize}>{t('useElderGoTitle')}</HelpPageTitle>

      <HelpCallout baseFontSize={baseFontSize} variant="warning">
        <span className="flex items-start gap-4">
          <span className="w-14 h-14 bg-eldergo-warning rounded-full flex items-center justify-center flex-shrink-0 inline-flex">
            <User size={28 * baseFontSize} strokeWidth={2.5} className="text-white" />
          </span>
          <span>
            <span className="block font-semibold mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
              {t('meetMrTan')}
            </span>
            <span className="block font-normal text-eldergo-muted" style={{ fontSize: `${17 * baseFontSize}px` }}>
              {t('mrTanIntro')}
            </span>
          </span>
        </span>
      </HelpCallout>

      <HelpStepCard
        baseFontSize={baseFontSize}
        title={t('step1Title')}
        icon={
          <span className="w-12 h-12 bg-eldergo-green/20 rounded-full flex items-center justify-center">
            <Sliders size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-green" />
          </span>
        }
        action={
          <HelpPrimaryButton baseFontSize={baseFontSize} variant="green" onClick={onNavigateToPreference}>
            {t('setMyPreference')}
          </HelpPrimaryButton>
        }
      >
        <HelpBodyText baseFontSize={baseFontSize}>{t('step1Body1')}</HelpBodyText>
        <HelpBodyText baseFontSize={baseFontSize}>{t('step1Body2')}</HelpBodyText>
      </HelpStepCard>

      <HelpStepCard
        baseFontSize={baseFontSize}
        title={t('step2Title')}
        icon={
          <span className="w-12 h-12 bg-eldergo-blue/20 rounded-full flex items-center justify-center">
            <MapPin size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
          </span>
        }
        action={
          <HelpPrimaryButton baseFontSize={baseFontSize} variant="blue" onClick={onNavigateToPlanning}>
            {t('tryPlanningRoute')}
          </HelpPrimaryButton>
        }
      >
        <HelpBodyText baseFontSize={baseFontSize}>{t('step2Body1')}</HelpBodyText>
        <HelpBodyText baseFontSize={baseFontSize}>{t('step2Body2')}</HelpBodyText>
      </HelpStepCard>

      <HelpStepCard
        baseFontSize={baseFontSize}
        title={t('step3Title')}
        icon={
          <span className="w-12 h-12 bg-eldergo-warning/20 rounded-full flex items-center justify-center">
            <HelpCircle size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-warning" />
          </span>
        }
      >
        <HelpBodyText baseFontSize={baseFontSize}>{t('step3Body1')}</HelpBodyText>
        <HelpBodyText baseFontSize={baseFontSize}>{t('step3Body2')}</HelpBodyText>
      </HelpStepCard>

      <HelpStepCard
        baseFontSize={baseFontSize}
        title={t('exploreStationInfo')}
        icon={
          <span className="w-12 h-12 bg-eldergo-navy/20 rounded-full flex items-center justify-center">
            <Building2 size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-navy" />
          </span>
        }
        action={
          <button
            type="button"
            onClick={onNavigateToStation}
            className="w-full bg-eldergo-navy hover:bg-eldergo-navy-dark text-white font-semibold py-4 rounded-xl transition-colors text-center"
            style={{ fontSize: `${18 * baseFontSize}px` }}
          >
            {t('viewStationInformation')}
          </button>
        }
      >
        <HelpBodyText baseFontSize={baseFontSize}>{t('stationInfoBody1')}</HelpBodyText>
        <HelpBodyText baseFontSize={baseFontSize}>{t('stationInfoBody2')}</HelpBodyText>
      </HelpStepCard>
    </HelpPageShell>
  );
}
