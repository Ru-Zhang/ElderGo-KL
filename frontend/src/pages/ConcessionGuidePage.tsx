import { CreditCard, CheckCircle } from 'lucide-react';
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
            {t('concessionGuideTitle')}
          </h2>

          <div className="space-y-6">
            <div className="bg-eldergo-green text-white p-6 rounded-2xl shadow-md">
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

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <h3 className="font-semibold text-eldergo-navy mb-4" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('concessionPrepareTitle')}
              </h3>
              <div className="flex items-center gap-3 bg-eldergo-bg p-4 rounded-xl">
                <CreditCard size={32 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
                <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {t('concessionMyKad')}
                </p>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-md">
              <h3 className="font-semibold text-eldergo-navy mb-4" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('concessionApplyStepsTitle')}
              </h3>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-eldergo-blue text-white rounded-full flex items-center justify-center font-bold flex-shrink-0" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    1
                  </div>
                  <div>
                    <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStepPrepareTitle')}</p>
                    <p className="text-eldergo-muted" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStepPrepareBody')}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-eldergo-blue text-white rounded-full flex items-center justify-center font-bold flex-shrink-0" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    2
                  </div>
                  <div>
                    <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStepCounterTitle')}</p>
                    <p className="text-eldergo-muted" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStepCounterBody')}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-eldergo-blue text-white rounded-full flex items-center justify-center font-bold flex-shrink-0" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    3
                  </div>
                  <div>
                    <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStepFormTitle')}</p>
                    <p className="text-eldergo-muted" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStepFormBody')}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-eldergo-green text-white rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle size={24 * baseFontSize} strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>{t('concessionStepCollectTitle')}</p>
                    <p className="text-eldergo-muted" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('concessionStepCollectBody')}</p>
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
