import { CreditCard, Coins } from 'lucide-react';
import HelpPageShell from '../components/help/HelpPageShell';
import {
  HelpBodyText,
  HelpCallout,
  HelpContentCard,
  HelpPageTitle,
  HelpSectionTitle,
} from '../components/help/HelpPrimitives';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';

interface TicketGuidePageProps {
  onNavigateToHelp: () => void;
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function TicketGuidePage({
  onNavigateToHelp,
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToPreference,
  onShowChatbot,
}: TicketGuidePageProps) {
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
      <HelpPageTitle baseFontSize={baseFontSize}>{t('ticketGuideTitle')}</HelpPageTitle>

      <HelpContentCard>
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 bg-eldergo-green/20 rounded-full flex items-center justify-center flex-shrink-0">
            <Coins size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-green" />
          </div>
          <HelpSectionTitle baseFontSize={baseFontSize}>{t('ticketMethodToken')}</HelpSectionTitle>
        </div>
        <HelpBodyText baseFontSize={baseFontSize} className="mb-4">
          {t('ticketTokenIntro')}
        </HelpBodyText>
        <ol className="space-y-3" style={{ fontSize: `${17 * baseFontSize}px` }}>
          <li className="flex gap-3 text-eldergo-muted leading-relaxed">
            <span className="font-bold text-eldergo-blue flex-shrink-0">1.</span>
            <span>
              <span className="font-semibold text-eldergo-navy">{t('ticketFindMachineTitle')}</span>{' '}
              {t('ticketFindMachineBody')}
            </span>
          </li>
          <li className="flex gap-3 text-eldergo-muted leading-relaxed">
            <span className="font-bold text-eldergo-blue flex-shrink-0">2.</span>
            <span>
              <span className="font-semibold text-eldergo-navy">{t('ticketSelectLanguageTitle')}</span>{' '}
              {t('ticketSelectLanguageBody')}
            </span>
          </li>
          <li className="flex gap-3 text-eldergo-muted leading-relaxed">
            <span className="font-bold text-eldergo-blue flex-shrink-0">3.</span>
            <span>
              <span className="font-semibold text-eldergo-navy">{t('ticketChooseDestinationTitle')}</span>{' '}
              {t('ticketChooseDestinationBody')}
            </span>
          </li>
          <li className="flex gap-3 text-eldergo-muted leading-relaxed">
            <span className="font-bold text-eldergo-blue flex-shrink-0">4.</span>
            <span>
              <span className="font-semibold text-eldergo-navy">{t('ticketPayTitle')}</span> {t('ticketPayBody')}
            </span>
          </li>
          <li className="flex gap-3 text-eldergo-muted leading-relaxed">
            <span className="font-bold text-eldergo-blue flex-shrink-0">5.</span>
            <span>
              <span className="font-semibold text-eldergo-navy">{t('ticketCollectTitle')}</span>{' '}
              {t('ticketCollectBody')}
            </span>
          </li>
        </ol>
      </HelpContentCard>

      <HelpContentCard>
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 bg-eldergo-blue/20 rounded-full flex items-center justify-center flex-shrink-0">
            <CreditCard size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
          </div>
          <HelpSectionTitle baseFontSize={baseFontSize}>{t('ticketMethodTouchNGo')}</HelpSectionTitle>
        </div>
        <HelpBodyText baseFontSize={baseFontSize} className="mb-3">
          <span className="font-semibold text-eldergo-green">{t('ticketHighlyRecommended')}</span> {t('ticketTouchNGoBody')}
        </HelpBodyText>
        <HelpBodyText baseFontSize={baseFontSize} className="mb-3">
          {t('ticketTouchNGoInstruction')}
        </HelpBodyText>
        <HelpBodyText baseFontSize={baseFontSize}>{t('ticketTouchNGoNoCard')}</HelpBodyText>
      </HelpContentCard>

      <HelpCallout baseFontSize={baseFontSize} variant="warning">
        <span className="block font-semibold mb-2" style={{ fontSize: `${18 * baseFontSize}px` }}>
          {t('ticketInfoSourceTitle')}
        </span>
        <span style={{ fontSize: `${17 * baseFontSize}px` }}>
          <a
            href="https://myrapid.com.my/"
            target="_blank"
            rel="noreferrer"
            className="font-semibold text-eldergo-blue underline"
          >
            {t('ticketInfoSourceBody')}
          </a>
        </span>
      </HelpCallout>
    </HelpPageShell>
  );
}
