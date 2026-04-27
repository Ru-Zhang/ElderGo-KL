import { useState } from 'react';
import { MapPin, Navigation, Lightbulb } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import PreferencesModal from '../components/common/PreferencesModal';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { getPlaceSuggestions } from '../services/googlePlaces';
import { PlaceSelection } from '../types/locations';

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
    onboardingCompleted,
    preferences,
    setOrigin: setRouteOrigin,
    setDestination: setRouteDestination
  } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

  const t = (key: string) => getTranslation(language, key as any);

  const [showPreferences, setShowPreferences] = useState(false);
  const [hasClickedInput, setHasClickedInput] = useState(false);
  const [startPoint, setStartPoint] = useState('');
  const [destination, setDestination] = useState('');
  const [selectedOrigin, setSelectedOrigin] = useState<PlaceSelection | null>(null);
  const [selectedDestination, setSelectedDestination] = useState<PlaceSelection | null>(null);
  const [startSuggestions, setStartSuggestions] = useState<PlaceSelection[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<PlaceSelection[]>([]);
  const [showStartDropdown, setShowStartDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  const [placesError, setPlacesError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const hasAnyPreferenceEnabled =
    preferences.accessibilityFirst || preferences.leastWalk || preferences.fewestTransfers;
  const shouldPromptPreferences = !onboardingCompleted && !hasAnyPreferenceEnabled;

  const toSuggestionLabel = (value: string) => {
    const parts = value
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean);

    if (parts.length === 0) return value;
    if (parts.length === 1) return parts[0];

    const firstPart = parts[0];
    if (/[A-Za-z]/.test(firstPart) && !/^\d+$/.test(firstPart)) {
      return firstPart;
    }

    const secondPart = parts[1];
    if (secondPart && /[A-Za-z]/.test(secondPart)) {
      return secondPart;
    }

    return firstPart;
  };

  const handleInputClick = () => {
    if (!hasClickedInput && shouldPromptPreferences) {
      setShowPreferences(true);
    }
    setHasClickedInput(true);
  };

  const handleStartChange = async (value: string) => {
    setStartPoint(value);
    setSelectedOrigin(null);
    setPlacesError(null);
    if (!value.trim()) {
      setFormError(null);
    }
    if (value.length > 0) {
      try {
        const suggestions = await getPlaceSuggestions(value);
        setStartSuggestions(suggestions);
        setPlacesError(null);
        if (suggestions.length === 0) {
          setFormError(t('invalidStartingPoint'));
        } else {
          setFormError(null);
        }
      } catch {
        setStartSuggestions([]);
        setPlacesError(t('googlePlacesUnavailable'));
      }
      setShowStartDropdown(true);
    } else {
      setShowStartDropdown(false);
    }
  };

  const handleDestChange = async (value: string) => {
    setDestination(value);
    setSelectedDestination(null);
    setPlacesError(null);
    if (!value.trim()) {
      setFormError(null);
    }
    if (value.length > 0) {
      try {
        const suggestions = await getPlaceSuggestions(value);
        setDestSuggestions(suggestions);
        setPlacesError(null);
        if (suggestions.length === 0) {
          setFormError(t('invalidDestination'));
        } else {
          setFormError(null);
        }
      } catch {
        setDestSuggestions([]);
        setPlacesError(t('googlePlacesUnavailable'));
      }
      setShowDestDropdown(true);
    } else {
      setShowDestDropdown(false);
    }
  };

  const handleSearch = () => {
    if (!startPoint && !destination) {
      setFormError(t('missingStartAndDestination'));
      return;
    }
    if (!startPoint) {
      setFormError(t('missingStartingPoint'));
      return;
    }
    if (!destination) {
      setFormError(t('missingDestination'));
      return;
    }

    const invalidStart = !selectedOrigin;
    const invalidDestination = !selectedDestination;

    if (invalidStart && invalidDestination) {
      setFormError(t('invalidStartAndDestination'));
      return;
    }
    if (invalidStart) {
      setFormError(t('invalidStartingPoint'));
      return;
    }
    if (invalidDestination) {
      setFormError(t('invalidDestination'));
      return;
    }

    setFormError(null);
    setRouteOrigin(selectedOrigin);
    setRouteDestination(selectedDestination);
    onNavigateToPlanTime();
  };

  return (
    <div className="min-h-screen bg-[#F5F7FA] relative" style={{ fontFamily: 'Poppins' }}>
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
              {placesError && (
                <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-4 rounded-xl text-[#1E3A5F] font-medium">
                  {placesError}
                </div>
              )}

              <p className="text-[#1E3A5F] font-semibold px-1" style={{ fontSize: `${16 * baseFontSize}px` }}>
                {t('startPointHint')}
              </p>
              <div className="relative">
                <div className="absolute left-5 top-1/2 -translate-y-1/2 z-30 pointer-events-none">
                  <Navigation
                    className="text-[#4A90E2]"
                    size={22 * baseFontSize}
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
                  className="w-full pl-16 pr-6 py-5 bg-white border-2 border-gray-300 rounded-xl font-medium text-[#1E3A5F] placeholder:text-gray-400 focus:outline-none focus:border-[#4A90E2] shadow-md relative z-10"
                  style={{ fontSize: `${18 * baseFontSize}px` }}
                />
                {showStartDropdown && startSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-gray-300 rounded-xl shadow-lg z-40 max-h-60 overflow-y-auto">
                    {startSuggestions.map((suggestion, index) => (
                      (() => {
                        const label = toSuggestionLabel(suggestion.displayName);
                        return (
                      <button
                        key={index}
                        onClick={() => {
                          setStartPoint(label);
                          setSelectedOrigin({ ...suggestion, displayName: label });
                          setShowStartDropdown(false);
                        }}
                        className="w-full px-6 py-4 text-left font-medium text-[#1E3A5F] hover:bg-[#F5F7FA] transition-colors border-b border-gray-200 last:border-b-0"
                        style={{ fontSize: `${18 * baseFontSize}px` }}
                      >
                        {label}
                      </button>
                        );
                      })()
                    ))}
                  </div>
                )}
              </div>

              <p className="text-[#1E3A5F] font-semibold px-1" style={{ fontSize: `${16 * baseFontSize}px` }}>
                {t('destinationHint')}
              </p>
              <div className="relative">
                <div className="absolute left-5 top-1/2 -translate-y-1/2 z-30 pointer-events-none">
                  <MapPin
                    className="text-[#E67E22]"
                    size={22 * baseFontSize}
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
                  className="w-full pl-16 pr-6 py-5 bg-white border-2 border-gray-300 rounded-xl font-medium text-[#1E3A5F] placeholder:text-gray-400 focus:outline-none focus:border-[#4A90E2] shadow-md relative z-10"
                  style={{ fontSize: `${18 * baseFontSize}px` }}
                />
                {showDestDropdown && destSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border-2 border-gray-300 rounded-xl shadow-lg z-40 max-h-60 overflow-y-auto">
                    {destSuggestions.map((suggestion, index) => (
                      (() => {
                        const label = toSuggestionLabel(suggestion.displayName);
                        return (
                      <button
                        key={index}
                        onClick={() => {
                          setDestination(label);
                          setSelectedDestination({ ...suggestion, displayName: label });
                          setShowDestDropdown(false);
                        }}
                        className="w-full px-6 py-4 text-left font-medium text-[#1E3A5F] hover:bg-[#F5F7FA] transition-colors border-b border-gray-200 last:border-b-0"
                        style={{ fontSize: `${18 * baseFontSize}px` }}
                      >
                        {label}
                      </button>
                        );
                      })()
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
              {formError && (
                <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-4 rounded-xl text-[#1E3A5F] font-medium">
                  {formError}
                </div>
              )}
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
