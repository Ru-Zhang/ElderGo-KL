import { CreditCard, Coins } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
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
  onShowChatbot
}: TicketGuidePageProps) {
  const { fontSize, language } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

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
        <div className="absolute inset-0 bg-white/42" />
        <div
          className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12'
          }}
        />
      </div>
      <div className="relative z-10">
      <TopBar onLogoClick={onNavigateToHelp} />

      <main className="pt-20 pb-32 px-6">
        <div className="max-w-2xl mx-auto">
          <h2 className="font-semibold text-eldergo-navy mb-8" style={{ fontSize: `${30 * baseFontSize}px` }}>
            {t('ticketGuideTitle')}
          </h2>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-eldergo-green/20 rounded-full flex items-center justify-center">
                  <Coins size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-green" />
                </div>
                <h3 className="font-semibold text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                  {t('ticketMethodToken')}
                </h3>
              </div>
              <p className="text-eldergo-muted leading-relaxed mb-4" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketTokenIntro')}
              </p>
              <ol className="space-y-3 text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <li className="flex gap-3">
                  <span className="font-bold text-eldergo-blue flex-shrink-0">1.</span>
                  <span><span className="font-semibold">{t('ticketFindMachineTitle')}</span> {t('ticketFindMachineBody')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-eldergo-blue flex-shrink-0">2.</span>
                  <span><span className="font-semibold">{t('ticketSelectLanguageTitle')}</span> {t('ticketSelectLanguageBody')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-eldergo-blue flex-shrink-0">3.</span>
                  <span><span className="font-semibold">{t('ticketChooseDestinationTitle')}</span> {t('ticketChooseDestinationBody')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-eldergo-blue flex-shrink-0">4.</span>
                  <span><span className="font-semibold">{t('ticketPayTitle')}</span> {t('ticketPayBody')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-eldergo-blue flex-shrink-0">5.</span>
                  <span><span className="font-semibold">{t('ticketCollectTitle')}</span> {t('ticketCollectBody')}</span>
                </li>
              </ol>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-eldergo-blue/20 rounded-full flex items-center justify-center">
                  <CreditCard size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
                </div>
                <h3 className="font-semibold text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                  {t('ticketMethodTouchNGo')}
                </h3>
              </div>
              <p className="text-eldergo-muted leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <span className="font-semibold text-eldergo-green">{t('ticketHighlyRecommended')}</span> {t('ticketTouchNGoBody')}
              </p>
              <p className="text-eldergo-muted leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketTouchNGoInstruction')}
              </p>
              <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketTouchNGoNoCard')}
              </p>
            </div>

            <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-6 rounded-xl">
              <p className="font-semibold text-eldergo-navy mb-2" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketInfoSourceTitle')}
              </p>
              <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <a
                  href="https://myrapid.com.my/"
                  target="_blank"
                  rel="noreferrer"
                  className="font-semibold text-eldergo-blue underline"
                >
                  {t('ticketInfoSourceBody')}
                </a>
              </p>
            </div>
          </div>
        </div>
      </main>

        <BottomNav
          activeTab="help"
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
