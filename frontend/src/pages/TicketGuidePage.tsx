import { ChevronLeft, CreditCard, Coins } from 'lucide-react';
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
          backgroundImage: 'url(/background-elder.jpg)',
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
      <TopBar />

      <main className="pt-20 pb-32 px-6">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={onNavigateToHelp}
            className="flex items-center gap-2 text-[#4A90E2] mb-6 hover:text-[#3A7FD2]"
          >
            <ChevronLeft size={24 * baseFontSize} strokeWidth={2.5} />
            <span className="font-medium" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('backToHelp')}</span>
          </button>

          <h2 className="font-semibold text-[#1E3A5F] mb-8" style={{ fontSize: `${30 * baseFontSize}px` }}>
            {t('ticketGuideTitle')}
          </h2>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-[#4A90E2]/20 rounded-full flex items-center justify-center">
                  <CreditCard size={28 * baseFontSize} strokeWidth={2.5} className="text-[#4A90E2]" />
                </div>
                <h3 className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                  {t('ticketMethod1Title')}
                </h3>
              </div>
              <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <span className="font-semibold text-[#6BBF59]">{t('ticketHighlyRecommended')}</span> {t('ticketMethod1Desc1')}
              </p>
              <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketMethod1Desc2')}
              </p>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-[#6BBF59]/20 rounded-full flex items-center justify-center">
                  <Coins size={28 * baseFontSize} strokeWidth={2.5} className="text-[#6BBF59]" />
                </div>
                <h3 className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                  {t('ticketMethod2Title')}
                </h3>
              </div>
              <p className="text-gray-700 leading-relaxed mb-4" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketMethod2Intro')}
              </p>
              <ol className="space-y-3 text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">1.</span>
                  <span><span className="font-semibold">{t('ticketStep1Title')}</span> {t('ticketStep1Body')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">2.</span>
                  <span><span className="font-semibold">{t('ticketStep2Title')}</span> {t('ticketStep2Body')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">3.</span>
                  <span><span className="font-semibold">{t('ticketStep3Title')}</span> {t('ticketStep3Body')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">4.</span>
                  <span><span className="font-semibold">{t('ticketStep4Title')}</span> {t('ticketStep4Body')}</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-bold text-[#4A90E2] flex-shrink-0">5.</span>
                  <span><span className="font-semibold">{t('ticketStep5Title')}</span> {t('ticketStep5Body')}</span>
                </li>
              </ol>
            </div>

            <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-6 rounded-xl">
              <p className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketNeedHelpTitle')}
              </p>
              <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('ticketNeedHelpBody')}
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
