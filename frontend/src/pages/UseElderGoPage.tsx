import { MapPin, Sliders, HelpCircle, ArrowRight, User, Building2 } from 'lucide-react';
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
          <h2 className="font-semibold text-eldergo-navy mb-6" style={{ fontSize: `${30 * baseFontSize}px` }}>
            {t('useElderGoTitle')}
          </h2>

          <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-6 rounded-xl mb-8 flex items-start gap-4">
            <div className="w-14 h-14 bg-eldergo-warning rounded-full flex items-center justify-center flex-shrink-0">
              <User size={28 * baseFontSize} strokeWidth={2.5} className="text-white" />
            </div>
            <div>
              <p className="font-semibold text-eldergo-navy mb-2" style={{ fontSize: `${20 * baseFontSize}px` }}>
                {t('meetMrTan')}
              </p>
              <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('mrTanIntro')}
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-eldergo-green/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Sliders size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-green" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-eldergo-navy mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('step1Title')}
                  </h3>
                  <p className="text-eldergo-muted leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step1Body1')}
                  </p>
                  <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step1Body2')}
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToPreference}
                className="w-full bg-eldergo-green hover:bg-eldergo-green-dark text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                {t('setMyPreference')}
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-eldergo-blue/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <MapPin size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-eldergo-navy mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('step2Title')}
                  </h3>
                  <p className="text-eldergo-muted leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step2Body1')}
                  </p>
                  <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step2Body2')}
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToPlanning}
                className="w-full bg-eldergo-blue hover:bg-eldergo-blue-dark text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
                style={{ fontSize: `${18 * baseFontSize}px` }}
              >
                {t('tryPlanningRoute')}
                <ArrowRight size={20 * baseFontSize} strokeWidth={2.5} />
              </button>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-eldergo-warning/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <HelpCircle size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-warning" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-eldergo-navy mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('step3Title')}
                  </h3>
                  <p className="text-eldergo-muted leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step3Body1')}
                  </p>
                  <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('step3Body2')}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-eldergo-navy/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Building2 size={24 * baseFontSize} strokeWidth={2.5} className="text-eldergo-navy" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-eldergo-navy mb-3" style={{ fontSize: `${22 * baseFontSize}px` }}>
                    {t('exploreStationInfo')}
                  </h3>
                  <p className="text-eldergo-muted leading-relaxed mb-3" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('stationInfoBody1')}
                  </p>
                  <p className="text-eldergo-muted leading-relaxed" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('stationInfoBody2')}
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToStation}
                className="w-full bg-eldergo-navy hover:bg-eldergo-navy-dark text-white font-semibold py-4 rounded-xl transition-colors flex items-center justify-center gap-2"
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
