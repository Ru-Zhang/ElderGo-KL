import { ChevronLeft, Shield, MapPinOff, Archive, Ban } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
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
  onShowChatbot
}: PrivacyInfoPageProps) {
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

          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 bg-[#6BBF59] rounded-full flex items-center justify-center">
              <Shield size={36 * baseFontSize} strokeWidth={2.5} className="text-white" />
            </div>
            <h2 className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${30 * baseFontSize}px` }}>
              {t('privacyTitle')}
            </h2>
          </div>

          <div className="bg-[#4A90E2] text-white p-6 rounded-2xl shadow-md mb-6">
            <h3 className="font-bold mb-3" style={{ fontSize: `${24 * baseFontSize}px` }}>
              {t('privacyPromiseTitle')}
            </h3>
            <p className="leading-relaxed" style={{ fontSize: `${20 * baseFontSize}px` }}>
              {t('privacyPromiseBody')}
            </p>
          </div>

          <div className="space-y-4">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 bg-[#6BBF59]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <MapPinOff size={28 * baseFontSize} strokeWidth={2.5} className="text-[#6BBF59]" />
                </div>
                <div>
                  <h4 className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                    {t('privacyNoLocationTitle')}
                  </h4>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('privacyNoLocationBody')}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 bg-[#4A90E2]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Archive size={28 * baseFontSize} strokeWidth={2.5} className="text-[#4A90E2]" />
                </div>
                <div>
                  <h4 className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                    {t('privacyNoHistoryTitle')}
                  </h4>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('privacyNoHistoryBody')}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 bg-[#E67E22]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Ban size={28 * baseFontSize} strokeWidth={2.5} className="text-[#E67E22]" />
                </div>
                <div>
                  <h4 className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                    {t('privacyNoAdsTitle')}
                  </h4>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('privacyNoAdsBody')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[#F5F7FA] border-2 border-[#4A90E2] p-6 rounded-2xl mt-6">
            <p className="text-[#1E3A5F] leading-relaxed text-center" style={{ fontSize: `${18 * baseFontSize}px` }}>
              {t('privacyFooter')}
            </p>
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
