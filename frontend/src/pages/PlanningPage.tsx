import { useEffect, useRef, useState } from 'react';
import { ArrowUpDown, MapPin, Navigation, Lightbulb } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import PreferencesModal from '../components/common/PreferencesModal';
import PlanningPlaceField from '../components/planning/PlanningPlaceField';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { getPlaceDetail, getPlaceSuggestions } from '../services/googlePlaces';
import { PlaceSelection } from '../types/locations';

const PLACES_DEBOUNCE_MS = 350;
const MIN_QUERY_LENGTH = 2;

interface PlanningPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToPlanTime: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onNavigateToUseElderGo: () => void;
  onShowChatbot: () => void;
}

function fieldValidationError(
  text: string,
  selected: PlaceSelection | null,
  missingMessage: string,
  invalidMessage: string,
  pickFromListMessage: string
): string | null {
  if (!text.trim()) {
    return missingMessage;
  }
  if (!selected?.googlePlaceId) {
    return text.trim() ? pickFromListMessage : invalidMessage;
  }
  return null;
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
    origin,
    preferences,
    destination: routeDestination,
    setOrigin: setRouteOrigin,
    setDestination: setRouteDestination
  } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

  const t = (key: string) => getTranslation(language, key as any);

  const [showPreferences, setShowPreferences] = useState(false);
  const [hasClickedInput, setHasClickedInput] = useState(false);
  const [startPoint, setStartPoint] = useState(origin?.displayName || '');
  const [destination, setDestination] = useState(routeDestination?.displayName || '');
  const [selectedOrigin, setSelectedOrigin] = useState<PlaceSelection | null>(origin);
  const [selectedDestination, setSelectedDestination] = useState<PlaceSelection | null>(routeDestination);
  const [startSuggestions, setStartSuggestions] = useState<PlaceSelection[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<PlaceSelection[]>([]);
  const [showStartDropdown, setShowStartDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  const [placesError, setPlacesError] = useState<string | null>(null);
  const [startFieldError, setStartFieldError] = useState<string | null>(null);
  const [destFieldError, setDestFieldError] = useState<string | null>(null);

  const startFieldRef = useRef<HTMLDivElement>(null);
  const destFieldRef = useRef<HTMLDivElement>(null);
  const startDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const destDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startRequestIdRef = useRef(0);
  const destRequestIdRef = useRef(0);

  const hasAnyPreferenceEnabled =
    preferences.accessibilityFirst || preferences.leastWalk || preferences.fewestTransfers;
  const shouldPromptPreferences = !onboardingCompleted && !hasAnyPreferenceEnabled;
  const chatPrefillNeedsConfirm =
    Boolean(origin?.displayName && !origin.googlePlaceId) ||
    Boolean(routeDestination?.displayName && !routeDestination.googlePlaceId);

  useEffect(() => {
    if (origin?.displayName) {
      setStartPoint(origin.displayName);
      setSelectedOrigin(origin);
    }
    if (routeDestination?.displayName) {
      setDestination(routeDestination.displayName);
      setSelectedDestination(routeDestination);
    }
  }, [origin?.displayName, routeDestination?.displayName]);

  useEffect(() => {
    return () => {
      if (startDebounceRef.current) clearTimeout(startDebounceRef.current);
      if (destDebounceRef.current) clearTimeout(destDebounceRef.current);
    };
  }, []);

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

  const scrollToFirstError = (startErr: string | null, destErr: string | null) => {
    requestAnimationFrame(() => {
      if (startErr && startFieldRef.current) {
        startFieldRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (destErr && destFieldRef.current) {
        destFieldRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  };

  const handleInputClick = () => {
    if (!hasClickedInput && shouldPromptPreferences) {
      setShowPreferences(true);
    }
    setHasClickedInput(true);
  };

  const clearStartField = () => {
    setStartPoint('');
    setSelectedOrigin(null);
    setStartSuggestions([]);
    setShowStartDropdown(false);
    setStartFieldError(null);
    setRouteOrigin(null);
  };

  const clearDestField = () => {
    setDestination('');
    setSelectedDestination(null);
    setDestSuggestions([]);
    setShowDestDropdown(false);
    setDestFieldError(null);
    setRouteDestination(null);
  };

  const fetchStartSuggestions = async (value: string) => {
    if (value.trim().length < MIN_QUERY_LENGTH) {
      setStartSuggestions([]);
      setShowStartDropdown(false);
      return;
    }

    const requestId = ++startRequestIdRef.current;
    try {
      const suggestions = await getPlaceSuggestions(value);
      if (requestId !== startRequestIdRef.current) return;

      setStartSuggestions(suggestions);
      setPlacesError(null);
      if (suggestions.length === 0) {
        setStartFieldError(t('invalidStartingPoint'));
        setShowStartDropdown(false);
      } else {
        setStartFieldError(null);
        setShowStartDropdown(true);
      }
    } catch {
      if (requestId !== startRequestIdRef.current) return;
      setStartSuggestions([]);
      setShowStartDropdown(false);
      setPlacesError(t('googlePlacesUnavailable'));
    }
  };

  const fetchDestSuggestions = async (value: string) => {
    if (value.trim().length < MIN_QUERY_LENGTH) {
      setDestSuggestions([]);
      setShowDestDropdown(false);
      return;
    }

    const requestId = ++destRequestIdRef.current;
    try {
      const suggestions = await getPlaceSuggestions(value);
      if (requestId !== destRequestIdRef.current) return;

      setDestSuggestions(suggestions);
      setPlacesError(null);
      if (suggestions.length === 0) {
        setDestFieldError(t('invalidDestination'));
        setShowDestDropdown(false);
      } else {
        setDestFieldError(null);
        setShowDestDropdown(true);
      }
    } catch {
      if (requestId !== destRequestIdRef.current) return;
      setDestSuggestions([]);
      setShowDestDropdown(false);
      setPlacesError(t('googlePlacesUnavailable'));
    }
  };

  const handleStartChange = (value: string) => {
    setStartPoint(value);
    setSelectedOrigin(null);
    setPlacesError(null);
    setStartFieldError(null);

    if (startDebounceRef.current) clearTimeout(startDebounceRef.current);

    if (!value.trim()) {
      startRequestIdRef.current += 1;
      setStartSuggestions([]);
      setShowStartDropdown(false);
      return;
    }

    setShowStartDropdown(false);
    startDebounceRef.current = setTimeout(() => {
      void fetchStartSuggestions(value);
    }, PLACES_DEBOUNCE_MS);
  };

  const handleDestChange = (value: string) => {
    setDestination(value);
    setSelectedDestination(null);
    setPlacesError(null);
    setDestFieldError(null);

    if (destDebounceRef.current) clearTimeout(destDebounceRef.current);

    if (!value.trim()) {
      destRequestIdRef.current += 1;
      setDestSuggestions([]);
      setShowDestDropdown(false);
      return;
    }

    setShowDestDropdown(false);
    destDebounceRef.current = setTimeout(() => {
      void fetchDestSuggestions(value);
    }, PLACES_DEBOUNCE_MS);
  };

  const handleStartSelect = async (suggestion: PlaceSelection, label: string) => {
    setStartPoint(label);
    const baseSelection = { ...suggestion, displayName: label };
    setSelectedOrigin(baseSelection);
    setShowStartDropdown(false);
    setStartFieldError(null);
    if (!suggestion.googlePlaceId) return;
    try {
      const detail = await getPlaceDetail(suggestion.googlePlaceId);
      setSelectedOrigin(detail);
      setRouteOrigin(detail);
    } catch {
      setRouteOrigin(baseSelection);
    }
  };

  const handleDestSelect = async (suggestion: PlaceSelection, label: string) => {
    setDestination(label);
    const baseSelection = { ...suggestion, displayName: label };
    setSelectedDestination(baseSelection);
    setShowDestDropdown(false);
    setDestFieldError(null);
    if (!suggestion.googlePlaceId) return;
    try {
      const detail = await getPlaceDetail(suggestion.googlePlaceId);
      setSelectedDestination(detail);
      setRouteDestination(detail);
    } catch {
      setRouteDestination(baseSelection);
    }
  };

  const handleSwapOriginDestination = () => {
    const nextStart = destination;
    const nextDest = startPoint;
    const nextStartSel = selectedDestination;
    const nextDestSel = selectedOrigin;
    const nextStartErr = destFieldError;
    const nextDestErr = startFieldError;

    setStartPoint(nextStart);
    setDestination(nextDest);
    setSelectedOrigin(nextStartSel);
    setSelectedDestination(nextDestSel);
    setStartSuggestions([]);
    setDestSuggestions([]);
    setShowStartDropdown(false);
    setShowDestDropdown(false);
    setStartFieldError(nextStartErr);
    setDestFieldError(nextDestErr);
    setRouteOrigin(nextStartSel);
    setRouteDestination(nextDestSel);
  };

  const handleSearch = () => {
    const startErr = fieldValidationError(
      startPoint,
      selectedOrigin,
      t('missingStartingPoint'),
      t('invalidStartingPoint'),
      t('pickPlaceFromList')
    );
    const destErr = fieldValidationError(
      destination,
      selectedDestination,
      t('missingDestination'),
      t('invalidDestination'),
      t('pickPlaceFromList')
    );

    setStartFieldError(startErr);
    setDestFieldError(destErr);

    if (startErr || destErr) {
      scrollToFirstError(startErr, destErr);
      return;
    }

    setRouteOrigin(selectedOrigin);
    setRouteDestination(selectedDestination);
    onNavigateToPlanTime();
  };

  const searchDisabled = !startPoint.trim() && !destination.trim();

  return (
    <div className="min-h-screen bg-eldergo-bg relative" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: 'url(/background-elder.png)',
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
              className="flex items-center gap-3 bg-white/95 px-4 py-3 rounded-xl shadow-md text-eldergo-navy hover:text-eldergo-blue transition-colors group"
            >
              <Lightbulb size={24 * baseFontSize} strokeWidth={2.5} className="group-hover:text-eldergo-warning" />
              <span className="font-medium" style={{ fontSize: `${18 * baseFontSize}px` }}>{t('howToUse')}</span>
            </button>

            <div className="space-y-4">
              {chatPrefillNeedsConfirm && (
                <div className="bg-eldergo-blue/10 border-l-4 border-eldergo-blue p-4 rounded-xl text-eldergo-navy font-medium">
                  {t('chatConfirmPlaceFromList')}
                </div>
              )}
              {placesError && (
                <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-4 rounded-xl text-eldergo-navy font-medium">
                  {placesError}
                </div>
              )}

              <p className="text-eldergo-navy font-semibold px-1" style={{ fontSize: `${16 * baseFontSize}px` }}>
                {t('startPointHint')}
              </p>
              <PlanningPlaceField
                fieldRef={startFieldRef}
                icon={
                  <Navigation
                    className="text-eldergo-blue"
                    size={22 * baseFontSize}
                    strokeWidth={2.5}
                  />
                }
                placeholder={t('enterStartingPoint')}
                value={startPoint}
                clearAriaLabel={t('clearStartPoint')}
                fieldError={startFieldError}
                showDropdown={showStartDropdown}
                suggestions={startSuggestions}
                baseFontSize={baseFontSize}
                onValueChange={handleStartChange}
                onClear={clearStartField}
                onInputClick={handleInputClick}
                onFocus={() => {
                  setStartFieldError(null);
                  if (startPoint.trim() && startSuggestions.length > 0) {
                    setShowStartDropdown(true);
                  }
                }}
                onSelectSuggestion={handleStartSelect}
                toSuggestionLabel={toSuggestionLabel}
              />

              <div className="flex justify-center -my-1 px-1">
                <button
                  type="button"
                  onClick={handleSwapOriginDestination}
                  disabled={!startPoint && !destination}
                  aria-label={t('swapOriginDestination')}
                  title={t('swapOriginDestination')}
                  className="flex items-center justify-center w-12 h-12 bg-white border-2 border-eldergo-border rounded-full shadow-md text-eldergo-blue hover:border-eldergo-blue hover:bg-eldergo-bg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ArrowUpDown size={22 * baseFontSize} strokeWidth={2.5} aria-hidden />
                </button>
              </div>

              <p className="text-eldergo-navy font-semibold px-1" style={{ fontSize: `${16 * baseFontSize}px` }}>
                {t('destinationHint')}
              </p>
              <PlanningPlaceField
                fieldRef={destFieldRef}
                icon={
                  <MapPin
                    className="text-eldergo-warning"
                    size={22 * baseFontSize}
                    strokeWidth={2.5}
                  />
                }
                placeholder={t('enterDestination')}
                value={destination}
                clearAriaLabel={t('clearDestination')}
                fieldError={destFieldError}
                showDropdown={showDestDropdown}
                suggestions={destSuggestions}
                baseFontSize={baseFontSize}
                onValueChange={handleDestChange}
                onClear={clearDestField}
                onInputClick={handleInputClick}
                onFocus={() => {
                  setDestFieldError(null);
                  if (destination.trim() && destSuggestions.length > 0) {
                    setShowDestDropdown(true);
                  }
                }}
                onSelectSuggestion={handleDestSelect}
                toSuggestionLabel={toSuggestionLabel}
              />

              <button
                type="button"
                onClick={handleSearch}
                disabled={searchDisabled}
                className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl transition-colors shadow-md"
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
