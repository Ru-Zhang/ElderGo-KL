import { Check, ChevronLeft, X, AlertTriangle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { ImageWithFallback } from '../components/common/ImageWithFallback';
import { useAppContext } from '../app/AppProvider';

interface StationDetailPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onNavigateToHome: () => void;
  onShowChatbot: () => void;
}

export default function StationDetailPage({
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onNavigateToHome,
  onShowChatbot
}: StationDetailPageProps) {
  const { fontSize, selectedStation } = useAppContext();
  const baseFontSize = fontSize === 'large' ? 1.25 : 1;

  if (!selectedStation) {
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

          <main className="pt-20 pb-32 px-6">
            <div className="max-w-2xl mx-auto mt-8">
              <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-8 rounded-xl flex items-start gap-4">
                <AlertTriangle size={32 * baseFontSize} strokeWidth={2.5} className="text-[#E67E22] flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1E3A5F] mb-3" style={{ fontSize: `${24 * baseFontSize}px` }}>
                    Station not found
                  </h3>
                  <p className="text-gray-700 mb-6" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    We couldn't load the station details. This might be because the station data is not available or there was an error loading it.
                  </p>
                  <button
                    onClick={onNavigateToStation}
                    className="bg-[#4A90E2] hover:bg-[#3A7FD2] text-white font-semibold py-4 px-6 rounded-xl transition-colors shadow-md"
                    style={{ fontSize: `${18 * baseFontSize}px` }}
                  >
                    Back to Stations
                  </button>
                </div>
              </div>
            </div>
          </main>

          <BottomNav
            activeTab="station"
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

      <main className="pt-[72px] pb-32">
        <div className="relative h-80">
          <div className="absolute inset-0 bg-black/20" />
          <ImageWithFallback
            src={selectedStation.imageUrl || "https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop"}
            alt={`${selectedStation.name} station`}
            className="w-full h-full object-cover"
          />
          <button
            onClick={onNavigateToStation}
            className="absolute top-6 left-6 w-14 h-14 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-colors"
          >
            <ChevronLeft size={32 * baseFontSize} strokeWidth={2.5} className="text-[#1E3A5F]" />
          </button>
          <h1 className="absolute bottom-8 left-8 font-bold text-white drop-shadow-lg" style={{ fontSize: `${36 * baseFontSize}px` }}>
            {selectedStation.name}
          </h1>
        </div>

        <div className="max-w-3xl mx-auto px-6 mt-8 space-y-6">
          <div className="bg-white rounded-2xl shadow-lg p-8 space-y-6">
            <div className="flex items-center gap-5 min-h-[64px]">
              <div className={`w-12 h-12 ${selectedStation.wheelchairAccessible ? 'bg-[#6BBF59]/20' : 'bg-gray-200'} rounded-full flex items-center justify-center flex-shrink-0`}>
                {selectedStation.wheelchairAccessible ? (
                  <Check size={28 * baseFontSize} strokeWidth={3} className="text-[#6BBF59]" />
                ) : (
                  <X size={28 * baseFontSize} strokeWidth={3} className="text-gray-400" />
                )}
              </div>
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                Wheelchair accessible: <span className={`font-semibold ${selectedStation.wheelchairAccessible ? 'text-[#6BBF59]' : 'text-gray-500'}`}>
                  {selectedStation.wheelchairAccessible ? 'Yes' : 'Not available'}
                </span>
              </span>
            </div>

            <div className="h-px bg-gray-200" />

            <div className="flex items-center gap-5 min-h-[64px]">
              <div className={`w-12 h-12 ${selectedStation.elevatorAvailable ? 'bg-[#6BBF59]/20' : 'bg-gray-200'} rounded-full flex items-center justify-center flex-shrink-0`}>
                {selectedStation.elevatorAvailable ? (
                  <Check size={28 * baseFontSize} strokeWidth={3} className="text-[#6BBF59]" />
                ) : (
                  <X size={28 * baseFontSize} strokeWidth={3} className="text-gray-400" />
                )}
              </div>
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                Elevator available: <span className={`font-semibold ${selectedStation.elevatorAvailable ? 'text-[#6BBF59]' : 'text-gray-500'}`}>
                  {selectedStation.elevatorAvailable ? 'Yes' : 'Not available'}
                </span>
              </span>
            </div>

            <div className="h-px bg-gray-200" />

            <div className="flex items-center gap-5 min-h-[64px]">
              <div className={`w-12 h-12 ${selectedStation.ticketCounter ? 'bg-[#4A90E2]/20' : 'bg-gray-200'} rounded-full flex items-center justify-center flex-shrink-0`}>
                {selectedStation.ticketCounter ? (
                  <Check size={28 * baseFontSize} strokeWidth={3} className="text-[#4A90E2]" />
                ) : (
                  <X size={28 * baseFontSize} strokeWidth={3} className="text-gray-400" />
                )}
              </div>
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                Ticket counter: <span className={`font-semibold ${selectedStation.ticketCounter ? 'text-[#4A90E2]' : 'text-gray-500'}`}>
                  {selectedStation.ticketCounter ? 'Available' : 'Not available'}
                </span>
              </span>
            </div>

            <div className="h-px bg-gray-200" />

            <div className="flex items-center gap-5 min-h-[64px]">
              <div className="w-12 h-12 bg-[#E67E22]/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Check size={28 * baseFontSize} strokeWidth={3} className="text-[#E67E22]" />
              </div>
              <span className="font-medium text-[#1E3A5F]" style={{ fontSize: `${22 * baseFontSize}px` }}>
                Operating hours: <span className="font-semibold text-[#E67E22]">{selectedStation.operatingHours}</span>
              </span>
            </div>
          </div>

          <button className="w-full bg-[#E67E22] hover:bg-[#D35400] text-white font-semibold py-6 rounded-2xl transition-colors shadow-lg min-h-[80px]" style={{ fontSize: `${24 * baseFontSize}px` }}>
            Start Route from Here
          </button>
        </div>
      </main>

        <BottomNav
          activeTab="station"
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
