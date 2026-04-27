import { AlertTriangle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
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
  onShowChatbot
}: HelpPageProps) {
  const { fontSize, language } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

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
    <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: 'url(/background-elder.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-white/50 via-white/45 to-white/50" />
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
          <h3 className="font-semibold text-eldergo-navy mb-6" style={{ fontSize: `${24 * baseFontSize}px` }}>
            {t('appIssues')}
          </h3>

          <button
            onClick={handleReset}
            className="w-full bg-white border-3 border-eldergo-warning text-eldergo-warning font-semibold py-5 rounded-xl hover:bg-eldergo-warning hover:text-white transition-all shadow-md flex items-center justify-center gap-3 mb-4"
            style={{ fontSize: `${20 * baseFontSize}px` }}
          >
            <AlertTriangle size={24 * baseFontSize} strokeWidth={2.5} />
            {t('clearCacheReset')}
          </button>

          <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-5 rounded-xl mb-10">
            <p className="text-eldergo-navy font-medium" style={{ fontSize: `${16 * baseFontSize}px` }}>
              ⚠️ {t('clearCacheWarning')}
            </p>
          </div>

          <div className="h-px bg-gray-300 my-8"></div>

          <h2 className="font-semibold text-eldergo-navy mb-6" style={{ fontSize: `${24 * baseFontSize}px` }}>
            {t('helpHeading')}
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-10">
            <button
              onClick={onNavigateToUseElderGo}
              className="h-52 sm:h-56 bg-white border-2 border-eldergo-border hover:border-eldergo-blue p-5 sm:p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <img src="/icons/help-support.svg" alt="" className="w-20 h-20 flex-shrink-0" />
              <span className="min-h-[3.5rem] flex items-center justify-center font-semibold text-eldergo-navy text-center leading-tight" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('useElderGoCard')}
              </span>
            </button>

            <button
              onClick={onNavigateToTicketGuide}
              className="h-52 sm:h-56 bg-white border-2 border-eldergo-border hover:border-eldergo-green p-5 sm:p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <img src="/icons/ticket-guide.svg" alt="" className="w-20 h-20 flex-shrink-0" />
              <span className="min-h-[3.5rem] flex items-center justify-center font-semibold text-eldergo-navy text-center leading-tight" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('buyTicket')}
              </span>
            </button>

            <button
              onClick={onNavigateToConcessionGuide}
              className="h-52 sm:h-56 bg-white border-2 border-eldergo-border hover:border-eldergo-warning p-5 sm:p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <img src="/icons/concession.svg" alt="" className="w-20 h-20 flex-shrink-0" />
              <span className="min-h-[3.5rem] flex items-center justify-center font-semibold text-eldergo-navy text-center leading-tight" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('applyConcession')}
              </span>
            </button>

            <button
              onClick={onNavigateToPrivacyInfo}
              className="h-52 sm:h-56 bg-white border-2 border-eldergo-border hover:border-eldergo-navy p-5 sm:p-6 rounded-2xl shadow-md transition-all flex flex-col items-center justify-center gap-4"
            >
              <img src="/icons/privacy.svg" alt="" className="w-20 h-20 flex-shrink-0" />
              <span className="min-h-[3.5rem] flex items-center justify-center font-semibold text-eldergo-navy text-center leading-tight" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('privacyInfo')}
              </span>
            </button>
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
