import { Check, Sun, Sunset, Moon, Clock } from 'lucide-react';
import { useState } from 'react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { recommendRoute } from '../services/routesApi';
import { getTranslation } from '../i18n/translations';

interface PlanYourTimePageProps {
  onNavigateToPlanning: () => void;
  onNavigateToRouteResult: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function PlanYourTimePage({
  onNavigateToPlanning,
  onNavigateToRouteResult,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot
}: PlanYourTimePageProps) {
  const [selectedTime, setSelectedTime] = useState<'now' | 'morning' | 'afternoon' | 'evening'>('now');
  const {
    anonymousUserId,
    destination,
    fontSize,
    language,
    origin,
    preferences,
    routeLoading,
    setCurrentRoute,
    setDepartureTime,
    setRouteError,
    setRouteLoading
  } = useAppContext();

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const handleShowRoute = async () => {
    if (!origin || !destination) {
      setRouteError(t('planTimeMissingPoints'));
      onNavigateToPlanning();
      return;
    }

    const departureTime = selectedTime;
    setDepartureTime(departureTime);
    setRouteLoading(true);
    setRouteError(null);

    try {
      const route = await recommendRoute({
        anonymousUserId,
        origin,
        destination,
        departureTime,
        preferences
      });
      setCurrentRoute(route);
      onNavigateToRouteResult();
    } catch {
      setRouteError(t('planTimeUnableToRoute'));
    } finally {
      setRouteLoading(false);
    }
  };

  const timeOptions = [
    { value: 'now' as const, label: t('planTimeNow'), icon: Clock, description: t('planTimeNowDesc') },
    { value: 'morning' as const, label: t('planTimeMorning'), icon: Sun, description: t('planTimeMorningDesc') },
    { value: 'afternoon' as const, label: t('planTimeAfternoon'), icon: Sunset, description: t('planTimeAfternoonDesc') },
    { value: 'evening' as const, label: t('planTimeEvening'), icon: Moon, description: t('planTimeEveningDesc') }
  ];

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
        <div className="absolute inset-0 bg-white/40" />
        <div
          className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12'
          }}
        />
      </div>
      <div className="relative z-10">
      <TopBar onLogoClick={onNavigateToPlanning} />

      <main className="pt-20 pb-40 px-6">
        <div className="max-w-2xl mx-auto mt-8">
          <h2 className="font-semibold text-eldergo-navy mb-8" style={{ fontSize: `${30 * baseFontSize}px` }}>
            {t('planTimeTitle')}
          </h2>

          <div className="space-y-4 mb-8">
            {timeOptions.map((option) => {
              const IconComponent = option.icon;
              const isSelected = selectedTime === option.value;

              return (
                <button
                  key={option.value}
                  onClick={() => setSelectedTime(option.value)}
                  className={`w-full p-6 rounded-2xl shadow-md transition-all flex items-center gap-5 ${
                    isSelected
                      ? 'bg-white border-3 border-eldergo-blue'
                      : 'bg-white border-2 border-eldergo-border hover:border-eldergo-border'
                  }`}
                >
                  <div className={`w-14 h-14 rounded-full flex items-center justify-center ${
                    isSelected ? 'bg-eldergo-blue' : 'bg-eldergo-bg'
                  }`}>
                    <IconComponent
                      size={28 * baseFontSize}
                      strokeWidth={2.5}
                      className={isSelected ? 'text-white' : 'text-eldergo-navy'}
                    />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-semibold text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                      {option.label}
                    </div>
                    <div className="text-eldergo-muted" style={{ fontSize: `${16 * baseFontSize}px` }}>
                      {option.description}
                    </div>
                  </div>
                  {isSelected && (
                    <Check size={32 * baseFontSize} strokeWidth={3} className="text-eldergo-blue" />
                  )}
                </button>
              );
            })}
          </div>

          <button
            onClick={handleShowRoute}
            disabled={routeLoading}
            className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark text-white font-semibold py-5 rounded-xl transition-colors shadow-lg"
            style={{ fontSize: `${22 * baseFontSize}px` }}
          >
            {routeLoading ? t('planTimeFindingRoute') : t('planTimeShowRoute')}
          </button>
        </div>
      </main>

        <BottomNav
          activeTab="planning"
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
