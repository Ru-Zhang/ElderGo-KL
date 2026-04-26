import { useState, useRef } from 'react';
import { Download, Share2, Cloud, Train, MapPin, Check, Footprints, ChevronLeft, ChevronRight } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';

interface RouteResultPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function RouteResultPage({
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot
}: RouteResultPageProps) {
  const [viewMode, setViewMode] = useState<'text' | 'map'>('text');
  const [currentStep, setCurrentStep] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { currentRoute, fontSize, routeError } = useAppContext();

  const routeSteps = currentRoute?.steps.map((step) => ({
    step: step.step_number,
    title: step.instruction,
    duration: step.duration_minutes ? `${step.duration_minutes} min` : 'Time unknown',
    distance: step.distance_meters ? `${step.distance_meters}m` : step.transit_line || '',
    icon: step.step_type === 'walking' ? Footprints : step.step_type === 'transit' ? Train : MapPin,
    color: step.step_type === 'walking' ? '#4A90E2' : step.step_type === 'transit' ? '#6BBF59' : '#E67E22',
    accessibility: step.annotation.message
  })) || [];

  const scroll = (direction: 'left' | 'right') => {
    if (direction === 'left' && currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else if (direction === 'right' && currentStep < routeSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

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
        <div className="absolute inset-0 bg-white/35" />
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

      <main className="pt-20 pb-44 px-6">
        <div className="max-w-2xl mx-auto mt-6">
          {!currentRoute && (
            <div className="bg-white/95 p-6 rounded-2xl shadow-md mb-6">
              <h3 className="text-[24px] font-semibold text-[#1E3A5F] mb-3">
                No route selected yet
              </h3>
              <p className="text-[18px] text-gray-700 mb-5">
                {routeError || 'Please plan a route first so ElderGo KL can show one recommended route.'}
              </p>
              <button
                onClick={onNavigateToPlanning}
                className="w-full bg-[#E67E22] hover:bg-[#D35400] text-white font-semibold py-4 rounded-xl transition-colors shadow-md"
              >
                Plan a Route
              </button>
            </div>
          )}

          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setViewMode('text')}
              className={`flex-1 py-3 rounded-full font-semibold text-[18px] transition-all ${
                viewMode === 'text'
                  ? 'bg-[#4A90E2] text-white'
                  : 'bg-white text-[#1E3A5F] border-2 border-gray-300'
              }`}
            >
              Text View
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex-1 py-3 rounded-full font-semibold text-[18px] transition-all ${
                viewMode === 'map'
                  ? 'bg-[#4A90E2] text-white'
                  : 'bg-white text-[#1E3A5F] border-2 border-gray-300'
              }`}
            >
              Map View
            </button>
          </div>

          <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-5 rounded-xl mb-6 flex items-center gap-4">
            <Cloud size={28} strokeWidth={2.5} className="text-[#E67E22]" />
            <span className="text-[18px] font-medium text-[#1E3A5F]">
              Weather guidance is not connected yet. Accessibility notes use verified or unknown labels only.
            </span>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-md mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-[24px] font-semibold text-[#1E3A5F]">
                  {currentRoute ? `${currentRoute.origin_name} to ${currentRoute.destination_name}` : 'Route not selected'}
                </h3>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-[20px] font-bold text-[#4A90E2]">{currentRoute?.duration_minutes ?? '-'} mins</div>
                <div className="text-[14px] text-gray-600">Time</div>
              </div>
              <div>
                <div className="text-[20px] font-bold text-[#4A90E2]">{currentRoute?.transfers ?? '-'}</div>
                <div className="text-[14px] text-gray-600">Transfers</div>
              </div>
              <div>
                <div className="text-[20px] font-bold text-[#4A90E2]">{currentRoute?.walking_distance_meters ?? '-'}m</div>
                <div className="text-[14px] text-gray-600">Walk</div>
              </div>
            </div>
          </div>

          {viewMode === 'text' ? (
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-[20px] font-semibold text-[#1E3A5F]" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  Step by Step
                </h4>
                <div className="flex gap-2">
                  <button
                    onClick={() => scroll('left')}
                    className="w-12 h-12 bg-[#4A90E2] hover:bg-[#3A7FD2] rounded-full flex items-center justify-center transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={currentStep === 0}
                  >
                    <Download size={22} strokeWidth={2.5} className="text-white" />
                  </button>
                  <button
                    onClick={() => scroll('right')}
                    className="w-12 h-12 bg-[#6BBF59] hover:bg-[#5AAF49] rounded-full flex items-center justify-center transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={currentStep === routeSteps.length - 1}
                  >
                    <Share2 size={22} strokeWidth={2.5} className="text-white" />
                  </button>
                </div>
              </div>

              <div className="relative">
                <button
                  onClick={() => scroll('left')}
                  className="absolute left-2 top-1/2 -translate-y-1/2 z-10 w-12 h-12 bg-white/95 backdrop-blur-sm border-2 border-gray-300 rounded-full flex items-center justify-center hover:bg-white hover:border-[#4A90E2] transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={currentStep === 0}
                >
                  <ChevronLeft size={24} strokeWidth={2.5} className="text-[#1E3A5F]" />
                </button>

                <button
                  onClick={() => scroll('right')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 z-10 w-12 h-12 bg-white/95 backdrop-blur-sm border-2 border-gray-300 rounded-full flex items-center justify-center hover:bg-white hover:border-[#4A90E2] transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={currentStep === routeSteps.length - 1}
                >
                  <ChevronRight size={24} strokeWidth={2.5} className="text-[#1E3A5F]" />
                </button>

                <div className="overflow-hidden">
                  <div
                    className="flex transition-transform duration-300 ease-in-out"
                    style={{ transform: `translateX(-${currentStep * 100}%)` }}
                  >
                    {routeSteps.map((step) => {
                      const IconComponent = step.icon;
                      return (
                        <div
                          key={step.step}
                          className="w-full flex-shrink-0 px-16"
                        >
                          <div
                            className="bg-white/95 backdrop-blur-sm p-6 rounded-2xl shadow-xl border-l-4"
                            style={{ borderLeftColor: step.color }}
                          >
                            <div className="flex items-start gap-4">
                              <div
                                className="w-14 h-14 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0"
                                style={{
                                  backgroundColor: step.color,
                                  fontSize: `${18 * baseFontSize}px`
                                }}
                              >
                                {step.step}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-gray-500 mb-2" style={{ fontSize: `${12 * baseFontSize}px` }}>
                                  Step {step.step} of {routeSteps.length}
                                </div>
                                <div className="flex items-center gap-3 mb-3">
                                  <IconComponent size={24 * baseFontSize} style={{ color: step.color }} strokeWidth={2.5} />
                                  <div className="font-semibold text-[#1E3A5F]" style={{ fontSize: `${18 * baseFontSize}px` }}>
                                    {step.title}
                                  </div>
                                </div>
                                <div className="text-gray-700 mb-4" style={{ fontSize: `${16 * baseFontSize}px` }}>
                                  Duration: {step.duration} • {step.distance}
                                </div>
                                <div
                                  className="flex items-center gap-2 px-4 py-3 rounded-lg"
                                  style={{ backgroundColor: `${step.color}20` }}
                                >
                                  <Check size={20 * baseFontSize} strokeWidth={2.5} style={{ color: step.color }} />
                                  <span className="font-medium" style={{ color: step.color, fontSize: `${14 * baseFontSize}px` }}>
                                    {step.accessibility}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white p-4 rounded-2xl shadow-md">
              <iframe
                src="https://www.google.com/maps/embed?pb=!1m28!1m12!1m3!1d31912.163953713316!2d101.68658!3d3.1479!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!4m13!3e3!4m5!1s0x31cc49c701efeae7%3A0xf4d98e5b2f1c287d!2sKL%20Sentral!3m2!1d3.1334853!2d101.6859016!4m5!1s0x31cc37d5bf524375%3A0x73c598d5e4667c2!2sBukit%20Bintang%2C%20Kuala%20Lumpur!3m2!1d3.1477739!2d101.7100803!5e0!3m2!1sen!2s!4v1234567890&hl=en"
                width="100%"
                height="400"
                style={{ border: 0, borderRadius: '12px' }}
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>
          )}
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
