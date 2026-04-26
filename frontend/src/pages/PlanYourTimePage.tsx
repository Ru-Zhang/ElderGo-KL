import { Check, Sun, Sunset, Moon, Clock } from 'lucide-react';
import { useState } from 'react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { recommendRoute } from '../services/routesApi';

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
  const [selectedTime, setSelectedTime] = useState('Now');
  const {
    anonymousUserId,
    destination,
    fontSize,
    origin,
    preferences,
    routeLoading,
    setCurrentRoute,
    setDepartureTime,
    setRouteError,
    setRouteLoading
  } = useAppContext();

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

  const handleShowRoute = async () => {
    if (!origin || !destination) {
      setRouteError('Please choose your starting point and destination first.');
      onNavigateToPlanning();
      return;
    }

    const departureTime = selectedTime === 'Now' ? 'now' : selectedTime.toLowerCase();
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
      setRouteError('Unable to get a route right now. Please try again.');
    } finally {
      setRouteLoading(false);
    }
  };

  const timeOptions = [
    { label: 'Now', icon: Clock, description: 'Leave immediately' },
    { label: 'Morning', icon: Sun, description: '6:00 AM - 12:00 PM' },
    { label: 'Afternoon', icon: Sunset, description: '12:00 PM - 6:00 PM' },
    { label: 'Evening', icon: Moon, description: '6:00 PM - 12:00 AM' }
  ];

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
      <TopBar />

      <main className="pt-20 pb-40 px-6">
        <div className="max-w-2xl mx-auto mt-8">
          <h2 className="font-semibold text-[#1E3A5F] mb-8" style={{ fontSize: `${30 * baseFontSize}px` }}>
            When are you leaving?
          </h2>

          <div className="space-y-4 mb-8">
            {timeOptions.map((option) => {
              const IconComponent = option.icon;
              const isSelected = selectedTime === option.label;

              return (
                <button
                  key={option.label}
                  onClick={() => setSelectedTime(option.label)}
                  className={`w-full p-6 rounded-2xl shadow-md transition-all flex items-center gap-5 ${
                    isSelected
                      ? 'bg-white border-3 border-[#4A90E2]'
                      : 'bg-white border-2 border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className={`w-14 h-14 rounded-full flex items-center justify-center ${
                    isSelected ? 'bg-[#4A90E2]' : 'bg-gray-100'
                  }`}>
                    <IconComponent
                      size={28 * baseFontSize}
                      strokeWidth={2.5}
                      className={isSelected ? 'text-white' : 'text-[#1E3A5F]'}
                    />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                      {option.label}
                    </div>
                    <div className="text-gray-600" style={{ fontSize: `${16 * baseFontSize}px` }}>
                      {option.description}
                    </div>
                  </div>
                  {isSelected && (
                    <Check size={32 * baseFontSize} strokeWidth={3} className="text-[#4A90E2]" />
                  )}
                </button>
              );
            })}
          </div>

          <button
            onClick={handleShowRoute}
            disabled={routeLoading}
            className="w-full bg-[#E67E22] hover:bg-[#D35400] text-white font-semibold py-5 rounded-xl transition-colors shadow-lg"
            style={{ fontSize: `${22 * baseFontSize}px` }}
          >
            {routeLoading ? 'Finding Route...' : 'Show My Route'}
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
