import { useState } from 'react';
import { MapPin, Navigation, Lightbulb } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import PreferencesModal from '../components/common/PreferencesModal';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { getPlaceSuggestions } from '../services/googlePlaces';

interface PlanningPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToPlanTime: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onNavigateToUseElderGo: () => void;
  onShowChatbot: () => void;
}

export default function PlanningPage({
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToPlanTime,
  onNavigateToHelp,
  onNavigateToPreference,
  onNavigateToUseElderGo,
  onShowChatbot
}: PlanningPageProps) {
  const {
    fontSize,
    language,
    setOrigin: setRouteOrigin,
    setDestination: setRouteDestination
  } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

  const t = (key: string) => getTranslation(language, key as any);

  const [showPreferences, setShowPreferences] = useState(false);
  const [hasClickedInput, setHasClickedInput] = useState(false);
  const [startPoint, setStartPoint] = useState('');
  const [destination, setDestination] = useState('');
  const [startSuggestions, setStartSuggestions] = useState<string[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<string[]>([]);
  const [showStartDropdown, setShowStartDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);

  const popularLocations = [
    'KL Sentral',
    'Bukit Bintang',
    'Pasar Seni',
    'SunU-Monash',
    'KLCC',
    'Mid Valley',
    'Pavilion KL',
    'Sunway Pyramid'
  ];

  const handleInputClick = () => {
    if (!hasClickedInput) {
      setShowPreferences(true);
      setHasClickedInput(true);
    }
  };

  const handleStartChange = async (value: string) => {
    setStartPoint(value);
    if (value.length > 0) {
      try {
        const suggestions = await getPlaceSuggestions(value);
        setStartSuggestions(suggestions.map((suggestion) => suggestion.displayName));
      } catch {
        const filtered = popularLocations.filter(loc =>
          loc.toLowerCase().includes(value.toLowerCase())
        );
        setStartSuggestions(filtered);
      }
      setShowStartDropdown(true);
    } else {
      setShowStartDropdown(false);
    }
  };

  const handleDestChange = async (value: string) => {
    setDestination(value);
    if (value.length > 0) {
      try {
        const suggestions = await getPlaceSuggestions(value);
        setDestSuggestions(suggestions.map((suggestion) => suggestion.displayName));
      } catch {
        const filtered = popularLocations.filter(loc =>
          loc.toLowerCase().includes(value.toLowerCase())
        );
        setDestSuggestions(filtered);
      }
      setShowDestDropdown(true);
    } else {
      setShowDestDropdown(false);
    }
  };

  const handleSearch = () => {
    if (startPoint && destination) {
      setRouteOrigin({ displayName: startPoint });
      setRouteDestination({ displayName: destination });
      onNavigateToPlanTime();
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7FA] relative" style={{ fontFamily: 'Poppins' }}>
      <div className="absolute inset-0 z-0">
        <iframe
          src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d127642.74292114843!2d101.61300455!3d3.139003!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x31cc49c701efeae7%3A0xf4d98e5b2f1c287d!2sKuala%20Lumpur%2C%20Federal%20Territory%20of%20Kuala%20Lumpur%2C%20Malaysia!5e0!3m2!1sen!2s!4v1234567890&hl=en"
          width="100%"
          height="100%"
          style={{ border: 0 }}
          allowFullScreen
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
        />
      </div>

      <div className="relative z-10">
        <TopBar />

        <main className="pt-20 pb-32 px-6">
          <div className="max-w-2xl mx-auto space-y-6 mt-8">
            <button
              onClick={onNavigateToUseElderGo}
              className="flex items-center gap-3 bg-white/95 px-4 py-3 rounded-xl shadow-md text-[#1E3A5F] hover:text-[#4A90E2] transition-colors group"
            >
              <Lightbulb size={24 * baseFontSize} strokeWidth={2.5} className="group-hover:text-[#E67E22]" />
              <span className="font-medium" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('howToUse')}</span>
            </button>

            <div className="space-y-4">
              <div className="relative">
                <div className="absolute left-5 top-1/2 -translate-y-1/2 z-10 w-10 h-10 bg-[#4A90E2] rounded-full flex items-center justify-center shadow-md">
                  <Navigation
                    className="text-white"
                    size={20 * baseFontSize}
                    strokeWidth={2.5}
                  />
                </div>
                <input
                  type="text"
                  placeholder={t('enterStartingPoint')}
                  value={startPoint}
                  onChange={(e) => handleStartChange(e.target.value)}
                  onClick={handleInputClick}
                  onFocus={() => startPoint && setShowStartDropdown(true)}
                  className="w-full pl-20 pr-6 py-5 bg-white border-2 border-gray-300 rounded-xl font-medium text-[#1E3A5F] placeholder:text-gray-400 focus:outline-none focus:border-[#4A90E2] shadow-md relative z-10"
                  style={{ fontSize: `${18 * baseFontSize}px` }}
                />
                {showStartDropdown && startSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-gray-300 rounded-xl shadow-lg z-20 max-h-60 overflow-y-auto">
                    {startSuggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          setStartPoint(suggestion);
                          setShowStartDropdown(false);
                        }}
                        className="w-full px-6 py-4 text-left font-medium text-[#1E3A5F] hover:bg-[#F5F7FA] transition-colors border-b border-gray-200 last:border-b-0"
                        style={{ fontSize: `${18 * baseFontSize}px` }}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="relative">
                <div className="absolute left-5 top-1/2 -translate-y-1/2 z-10 w-10 h-10 bg-[#E67E22] rounded-full flex items-center justify-center shadow-md">
                  <MapPin
                    className="text-white"
                    size={20 * baseFontSize}
                    strokeWidth={2.5}
                  />
                </div>
                <input
                  type="text"
                  placeholder={t('enterDestination')}
                  value={destination}
                  onChange={(e) => handleDestChange(e.target.value)}
                  onClick={handleInputClick}
                  onFocus={() => destination && setShowDestDropdown(true)}
                  className="w-full pl-20 pr-6 py-5 bg-white border-2 border-gray-300 rounded-xl font-medium text-[#1E3A5F] placeholder:text-gray-400 focus:outline-none focus:border-[#4A90E2] shadow-md relative z-10"
                  style={{ fontSize: `${18 * baseFontSize}px` }}
                />
                {showDestDropdown && destSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-gray-300 rounded-xl shadow-lg z-20 max-h-60 overflow-y-auto">
                    {destSuggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          setDestination(suggestion);
                          setShowDestDropdown(false);
                        }}
                        className="w-full px-6 py-4 text-left font-medium text-[#1E3A5F] hover:bg-[#F5F7FA] transition-colors border-b border-gray-200 last:border-b-0"
                        style={{ fontSize: `${18 * baseFontSize}px` }}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={handleSearch}
                disabled={!startPoint || !destination}
                className="w-full bg-[#E67E22] hover:bg-[#D35400] disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl transition-colors shadow-md"
                style={{ fontSize: `${20 * baseFontSize}px` }}
              >
                {t('search')}
              </button>
            </div>
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

        <PreferencesModal
          isOpen={showPreferences}
          onClose={() => setShowPreferences(false)}
        />
      </div>
    </div>
  );
}
