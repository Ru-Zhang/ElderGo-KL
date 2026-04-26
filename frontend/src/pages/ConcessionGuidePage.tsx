import { ChevronLeft, CreditCard, CheckCircle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
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
  onShowChatbot
}: ConcessionGuidePageProps) {
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
            {t('concessionTitle')}
          </h2>

          <div className="space-y-6">
            <div className="bg-[#6BBF59] text-white p-6 rounded-2xl shadow-md">
              <h3 className="font-bold mb-3" style={{ fontSize: `${24 * baseFontSize}px` }}>
                {t('concessionBenefitTitle')}
              </h3>
              <p className="leading-relaxed" style={{ fontSize: `${20 * baseFontSize}px` }}>
                {t('concessionBenefitBodyPrefix')} <span className="font-bold">{t('concessionAgeHighlight')}</span> {t('concessionBenefitBodyMiddle')} <span className="font-bold" style={{ fontSize: `${28 * baseFontSize}px` }}>{t('concessionDiscountHighlight')}</span> {t('concessionBenefitBodySuffix')}
              </p>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <h3 className="font-semibold text-[#1E3A5F] mb-4" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('concessionPrepareTitle')}
              </h3>
              <div className="flex items-center gap-3 bg-[#F5F7FA] p-4 rounded-xl">
                <CreditCard size={32 * baseFontSize} strokeWidth={2.5} className="text-[#4A90E2]" />
                <p className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {t('concessionPrepareItem')}
                </p>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <h3 className="font-semibold text-[#1E3A5F] mb-4" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('concessionHowToApplyTitle')}
              </h3>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-[#4A90E2] text-white rounded-full flex items-center justify-center font-bold flex-shrink-0" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    1
                  </div>
                  <div>
                    <p className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStep1Title')}</p>
                    <p className="text-gray-700" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStep1Body')}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-[#4A90E2] text-white rounded-full flex items-center justify-center font-bold flex-shrink-0" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    2
                  </div>
                  <div>
                    <p className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStep2Title')}</p>
                    <p className="text-gray-700" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStep2Body')}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-[#4A90E2] text-white rounded-full flex items-center justify-center font-bold flex-shrink-0" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    3
                  </div>
                  <div>
                    <p className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStep3Title')}</p>
                    <p className="text-gray-700" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStep3Body')}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-[#6BBF59] text-white rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle size={24 * baseFontSize} strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStep4Title')}</p>
                    <p className="text-gray-700" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStep4Body')}</p>
                  </div>
                </div>
              </div>
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
