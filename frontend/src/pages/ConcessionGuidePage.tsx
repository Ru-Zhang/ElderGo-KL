import { CreditCard, CheckCircle } from 'lucide-react';
import HelpPageShell from '../components/help/HelpPageShell';
import {
  HelpBodyText,
  HelpContentCard,
  HelpPageTitle,
  HelpSectionTitle,
} from '../components/help/HelpPrimitives';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';

interface ConcessionGuidePageProps {
  onNavigateToHelp: () => void;
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function ConcessionGuidePage({
  onNavigateToHelp,
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToPreference,
  onShowChatbot,
}: ConcessionGuidePageProps) {
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
      <HelpPageTitle baseFontSize={baseFontSize}>{t('concessionGuideTitle')}</HelpPageTitle>

      <div className="bg-eldergo-green text-white p-6 rounded-2xl shadow-md border border-eldergo-green">
        <h3 className="font-bold mb-3" style={{ fontSize: `${24 * baseFontSize}px` }}>
          {t('concessionBenefitTitle')}
        </h3>
        <p className="leading-relaxed" style={{ fontSize: `${20 * baseFontSize}px` }}>
          {t('concessionBenefitPrefix')}{' '}
          <span
            className="font-extrabold text-eldergo-warning-bg bg-eldergo-warning px-3 py-1 rounded-lg inline-block"
            style={{ fontSize: `${30 * baseFontSize}px` }}
          >
            {t('concessionBenefitHighlight')}
          </span>{' '}
          {t('concessionBenefitSuffix')}
        </p>
      </div>

      <HelpContentCard>
        <HelpSectionTitle baseFontSize={baseFontSize}>{t('concessionPrepareTitle')}</HelpSectionTitle>
        <div className="flex items-center gap-3 bg-eldergo-bg p-4 rounded-xl mt-4">
          <CreditCard size={32 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
          <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>
            {t('concessionMyKad')}
          </p>
        </div>
      </HelpContentCard>

      <HelpContentCard>
        <HelpSectionTitle baseFontSize={baseFontSize}>{t('concessionApplyStepsTitle')}</HelpSectionTitle>
        <div className="space-y-4 mt-4">
          {[
            { n: '1', title: t('concessionStepPrepareTitle'), body: t('concessionStepPrepareBody') },
            { n: '2', title: t('concessionStepCounterTitle'), body: t('concessionStepCounterBody') },
            { n: '3', title: t('concessionStepFormTitle'), body: t('concessionStepFormBody') },
          ].map((step) => (
            <div key={step.n} className="flex items-start gap-4">
              <div
                className="w-10 h-10 bg-eldergo-blue text-white rounded-full flex items-center justify-center font-bold flex-shrink-0"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                {step.n}
              </div>
              <div>
                <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {step.title}
                </p>
                <HelpBodyText baseFontSize={baseFontSize}>{step.body}</HelpBodyText>
              </div>
            </div>
          ))}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-eldergo-green text-white rounded-full flex items-center justify-center flex-shrink-0">
              <CheckCircle size={24 * baseFontSize} strokeWidth={2.5} />
            </div>
            <div>
              <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>
                {t('concessionStepCollectTitle')}
              </p>
              <HelpBodyText baseFontSize={baseFontSize}>{t('concessionStepCollectBody')}</HelpBodyText>
            </div>
          </div>
        </div>
      </HelpContentCard>
    </HelpPageShell>
  );
}
