import { ChevronLeft, MapPin, Sliders, HelpCircle, ArrowRight, User, Building2 } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
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
  onShowChatbot
}: UseElderGoPageProps) {
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

          <h2 className="font-semibold text-[#1E3A5F] mb-6" style={{ fontSize: `${30 * baseFontSize}px` }}>
            {t('useElderGoTitle')}
          </h2>

          <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-6 rounded-xl mb-8 flex items-start gap-4">
            <div className="w-14 h-14 bg-[#E67E22] rounded-full flex items-center justify-center flex-shrink-0">
              <User size={28 * baseFontSize} strokeWidth={2.5} className="text-white" />
            </div>
            <div>
              <p className="font-semibold text-[#1E3A5F] mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                {t('meetMrTan')}
              </p>
              <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('mrTanIntro')}
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#6BBF59]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Sliders size={24 * baseFontSize} strokeWidth={2.5} className="text-[#6BBF59]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('step1Title')}
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step1Body1')}
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step1Body2')}
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToPreference}
                className="w-full bg-[#6BBF59] hover:bg-[#5AAF49] text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                {t('setMyPreference')}
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#4A90E2]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <MapPin size={24 * baseFontSize} strokeWidth={2.5} className="text-[#4A90E2]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('step2Title')}
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step2Body1')}
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step2Body2')}
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToPlanning}
                className="w-full bg-[#4A90E2] hover:bg-[#3A7FD2] text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                {t('tryPlanningRoute')}
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#E67E22]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <HelpCircle size={24 * baseFontSize} strokeWidth={2.5} className="text-[#E67E22]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('step3Title')}
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step3Body1')}
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step3Body2')}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-[#1E3A5F]/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Building2 size={24 * baseFontSize} strokeWidth={2.5} className="text-[#1E3A5F]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('exploreStationInfo')}
                  </h3>
                  <p className="text-gray-700 leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('stationInfoBody1')}
                  </p>
                  <p className="text-gray-700 leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('stationInfoBody2')}
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToStation}
                className="w-full bg-[#1E3A5F] hover:bg-[#15283F] text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                {t('viewStationInformation')}
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
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
