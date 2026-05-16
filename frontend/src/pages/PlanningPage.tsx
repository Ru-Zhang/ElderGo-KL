import { useEffect, useRef, useState } from 'react';
import { ArrowUpDown, MapPin, Navigation, Lightbulb } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import PreferencesModal from '../components/common/PreferencesModal';
import PlanningPlaceField from '../components/planning/PlanningPlaceField';
import { useAppContext } from '../app/AppProvider';
import { getTranslation, type TranslationKey } from '../i18n/translations';
import {
  getPlaceDetail,
  getPlaceSuggestions,
  resolvePlaceSelection,
} from '../services/googlePlaces';
import { PlaceSelection } from '../types/locations';
import {
  formatPlaceDisplayName,
  isPlaceResolved,
  placeSelectionNeedsUserPick,
  placeTextsMatch,
  shouldAutoResolvePlace,
} from '../utils/placeDisplay';

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

type PlaceFieldErrorKey =
  | 'missingStartingPoint'
  | 'missingDestination'
  | 'invalidStartingPoint'
  | 'invalidDestination'
  | 'pickPlaceFromList';

function fieldValidationErrorKey(
  text: string,
  selected: PlaceSelection | null,
  missingKey: PlaceFieldErrorKey,
  invalidKey: PlaceFieldErrorKey,
  pickFromListKey: PlaceFieldErrorKey
): PlaceFieldErrorKey | null {
  if (!text.trim()) {
    return missingKey;
  }
  if (!isPlaceResolved(selected)) {
    return text.trim() ? pickFromListKey : invalidKey;
  }
  return null;
}

function applyResolvedPlace(
  resolved: PlaceSelection,
  setText: (value: string) => void,
  setSelected: (value: PlaceSelection) => void,
  setRoute: (value: PlaceSelection) => void
) {
  const label = formatPlaceDisplayName(resolved.displayName);
  setText(label);
  const next = { ...resolved, displayName: label };
  setSelected(next);
  setRoute(next);
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

  const t = (key: TranslationKey) => getTranslation(language, key);

  const [showPreferences, setShowPreferences] = useState(false);
  const [hasClickedInput, setHasClickedInput] = useState(false);
  const [startPoint, setStartPoint] = useState(formatPlaceDisplayName(origin?.displayName) || '');
  const [destination, setDestination] = useState(formatPlaceDisplayName(routeDestination?.displayName) || '');
  const [selectedOrigin, setSelectedOrigin] = useState<PlaceSelection | null>(origin);
  const [selectedDestination, setSelectedDestination] = useState<PlaceSelection | null>(routeDestination);
  const [startSuggestions, setStartSuggestions] = useState<PlaceSelection[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<PlaceSelection[]>([]);
  const [showStartDropdown, setShowStartDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  const [placesErrorKey, setPlacesErrorKey] = useState<'googlePlacesUnavailable' | null>(null);
  const [startFieldErrorKey, setStartFieldErrorKey] = useState<PlaceFieldErrorKey | null>(null);
  const [destFieldErrorKey, setDestFieldErrorKey] = useState<PlaceFieldErrorKey | null>(null);
  const placesError = placesErrorKey ? t(placesErrorKey) : null;
  const startFieldError = startFieldErrorKey ? t(startFieldErrorKey) : null;
  const destFieldError = destFieldErrorKey ? t(destFieldErrorKey) : null;
  const [resolvingStart, setResolvingStart] = useState(false);
  const [resolvingDest, setResolvingDest] = useState(false);

  const startFieldRef = useRef<HTMLDivElement>(null);
  const destFieldRef = useRef<HTMLDivElement>(null);
  const startDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const destDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startRequestIdRef = useRef(0);
  const destRequestIdRef = useRef(0);

  const shouldPromptPreferences = !onboardingCompleted;
  const showChatConfirmBanner =
    (placeSelectionNeedsUserPick(selectedOrigin) || placeSelectionNeedsUserPick(selectedDestination)) &&
    !(resolvingStart || resolvingDest);

  useEffect(() => {
    if (!origin?.displayName) return;

    const label = formatPlaceDisplayName(origin.displayName);
    setStartPoint(label);
    setSelectedOrigin({ ...origin, displayName: label });

    if (!shouldAutoResolvePlace(origin)) {
      return;
    }

    let cancelled = false;
    setResolvingStart(true);
    void resolvePlaceSelection(origin)
      .then((resolved) => {
        if (cancelled) return;
        applyResolvedPlace(resolved, setStartPoint, setSelectedOrigin, setRouteOrigin);
      })
      .finally(() => {
        if (!cancelled) setResolvingStart(false);
      });

    return () => {
      cancelled = true;
    };
  }, [origin, setRouteOrigin]);

  useEffect(() => {
    if (!routeDestination?.displayName) return;

    const label = formatPlaceDisplayName(routeDestination.displayName);
    setDestination(label);
    setSelectedDestination({ ...routeDestination, displayName: label });

    if (!shouldAutoResolvePlace(routeDestination)) {
      return;
    }

    let cancelled = false;
    setResolvingDest(true);
    void resolvePlaceSelection(routeDestination)
      .then((resolved) => {
        if (cancelled) return;
        applyResolvedPlace(resolved, setDestination, setSelectedDestination, setRouteDestination);
      })
      .finally(() => {
        if (!cancelled) setResolvingDest(false);
      });

    return () => {
      cancelled = true;
    };
  }, [routeDestination, setRouteDestination]);

  useEffect(() => {
    return () => {
      if (startDebounceRef.current) clearTimeout(startDebounceRef.current);
      if (destDebounceRef.current) clearTimeout(destDebounceRef.current);
    };
  }, []);

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
    setStartFieldErrorKey(null);
    setRouteOrigin(null);
  };

  const clearDestField = () => {
    setDestination('');
    setSelectedDestination(null);
    setDestSuggestions([]);
    setShowDestDropdown(false);
    setDestFieldErrorKey(null);
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
      setPlacesErrorKey(null);
      if (suggestions.length === 0) {
        setStartFieldErrorKey('invalidStartingPoint');
        setShowStartDropdown(false);
      } else {
        setStartFieldErrorKey(null);
        setShowStartDropdown(true);
      }
    } catch {
      if (requestId !== startRequestIdRef.current) return;
      setStartSuggestions([]);
      setShowStartDropdown(false);
      setPlacesErrorKey('googlePlacesUnavailable');
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
      setPlacesErrorKey(null);
      if (suggestions.length === 0) {
        setDestFieldErrorKey('invalidDestination');
        setShowDestDropdown(false);
      } else {
        setDestFieldErrorKey(null);
        setShowDestDropdown(true);
      }
    } catch {
      if (requestId !== destRequestIdRef.current) return;
      setDestSuggestions([]);
      setShowDestDropdown(false);
      setPlacesErrorKey('googlePlacesUnavailable');
    }
  };

  const tryResolveFieldOnBlur = async (
    text: string,
    selected: PlaceSelection | null,
    setText: (value: string) => void,
    setSelected: (value: PlaceSelection) => void,
    setRoute: (value: PlaceSelection) => void,
    setResolving: (value: boolean) => void,
    setFieldErrorKey: (value: PlaceFieldErrorKey | null) => void
  ) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    if (selected && isPlaceResolved(selected) && placeTextsMatch(trimmed, selected.displayName)) {
      setText(formatPlaceDisplayName(selected.displayName));
      return;
    }

    setResolving(true);
    try {
      const resolved = await resolvePlaceSelection({
        displayName: trimmed,
        lat: selected?.lat ?? null,
        lon: selected?.lon ?? null,
        googlePlaceId: selected?.googlePlaceId ?? null,
      });
      if (isPlaceResolved(resolved)) {
        applyResolvedPlace(resolved, setText, setSelected, setRoute);
        setFieldErrorKey(null);
      }
    } finally {
      setResolving(false);
    }
  };

  const handleStartChange = (value: string) => {
    setStartPoint(value);
    if (selectedOrigin && placeTextsMatch(value, selectedOrigin.displayName)) {
      setPlacesErrorKey(null);
      setStartFieldErrorKey(null);
      return;
    }
    setSelectedOrigin(null);
    setPlacesErrorKey(null);
    setStartFieldErrorKey(null);

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
    if (selectedDestination && placeTextsMatch(value, selectedDestination.displayName)) {
      setPlacesErrorKey(null);
      setDestFieldErrorKey(null);
      return;
    }
    setSelectedDestination(null);
    setPlacesErrorKey(null);
    setDestFieldErrorKey(null);

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
    const shortLabel = formatPlaceDisplayName(label);
    setStartPoint(shortLabel);
    const baseSelection = { ...suggestion, displayName: shortLabel };
    setSelectedOrigin(baseSelection);
    setShowStartDropdown(false);
    setStartFieldErrorKey(null);
    if (!suggestion.googlePlaceId) return;
    try {
      const detail = await getPlaceDetail(suggestion.googlePlaceId, shortLabel);
      setSelectedOrigin(detail);
      setRouteOrigin(detail);
    } catch {
      setRouteOrigin(baseSelection);
    }
  };

  const handleDestSelect = async (suggestion: PlaceSelection, label: string) => {
    const shortLabel = formatPlaceDisplayName(label);
    setDestination(shortLabel);
    const baseSelection = { ...suggestion, displayName: shortLabel };
    setSelectedDestination(baseSelection);
    setShowDestDropdown(false);
    setDestFieldErrorKey(null);
    if (!suggestion.googlePlaceId) return;
    try {
      const detail = await getPlaceDetail(suggestion.googlePlaceId, shortLabel);
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
    const nextStartErr = destFieldErrorKey;
    const nextDestErr = startFieldErrorKey;

    setStartPoint(nextStart);
    setDestination(nextDest);
    setSelectedOrigin(nextStartSel);
    setSelectedDestination(nextDestSel);
    setStartSuggestions([]);
    setDestSuggestions([]);
    setShowStartDropdown(false);
    setShowDestDropdown(false);
    setStartFieldErrorKey(nextStartErr);
    setDestFieldErrorKey(nextDestErr);
    setRouteOrigin(nextStartSel);
    setRouteDestination(nextDestSel);
  };

  const handleSearch = async () => {
    let originForSearch = selectedOrigin;
    let destinationForSearch = selectedDestination;

    if (startPoint.trim() && !isPlaceResolved(selectedOrigin)) {
      setResolvingStart(true);
      try {
        originForSearch = await resolvePlaceSelection({
          displayName: startPoint.trim(),
          lat: selectedOrigin?.lat ?? null,
          lon: selectedOrigin?.lon ?? null,
          googlePlaceId: selectedOrigin?.googlePlaceId ?? null,
        });
        if (isPlaceResolved(originForSearch)) {
          applyResolvedPlace(originForSearch, setStartPoint, setSelectedOrigin, setRouteOrigin);
        }
      } finally {
        setResolvingStart(false);
      }
    }

    if (destination.trim() && !isPlaceResolved(selectedDestination)) {
      setResolvingDest(true);
      try {
        destinationForSearch = await resolvePlaceSelection({
          displayName: destination.trim(),
          lat: selectedDestination?.lat ?? null,
          lon: selectedDestination?.lon ?? null,
          googlePlaceId: selectedDestination?.googlePlaceId ?? null,
        });
        if (isPlaceResolved(destinationForSearch)) {
          applyResolvedPlace(
            destinationForSearch,
            setDestination,
            setSelectedDestination,
            setRouteDestination
          );
        }
      } finally {
        setResolvingDest(false);
      }
    }

    const startErr = fieldValidationErrorKey(
      startPoint,
      originForSearch,
      'missingStartingPoint',
      'invalidStartingPoint',
      'pickPlaceFromList'
    );
    const destErr = fieldValidationErrorKey(
      destination,
      destinationForSearch,
      'missingDestination',
      'invalidDestination',
      'pickPlaceFromList'
    );

    setStartFieldErrorKey(startErr);
    setDestFieldErrorKey(destErr);

    if (startErr || destErr) {
      scrollToFirstError(startErr, destErr);
      return;
    }

    setRouteOrigin(originForSearch);
    setRouteDestination(destinationForSearch);
    onNavigateToPlanTime();
  };

  const searchDisabled =
    resolvingStart || resolvingDest || (!startPoint.trim() && !destination.trim());

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
              className="flex min-h-[52px] w-full items-center gap-3 rounded-xl bg-white/95 px-4 py-3 text-left shadow-md text-eldergo-navy transition-colors group hover:text-eldergo-blue"
            >
              <Lightbulb
                size={24 * baseFontSize}
                strokeWidth={2.5}
                className="shrink-0 group-hover:text-eldergo-warning"
              />
              <span className="font-medium leading-snug" style={{ fontSize: `${18 * baseFontSize}px` }}>
                {t('howToUse')}
              </span>
            </button>

            <div className="space-y-4">
              {showChatConfirmBanner && (
                <div className="bg-eldergo-blue/10 border-l-4 border-eldergo-blue p-4 rounded-xl text-eldergo-navy font-medium">
                  {t('chatConfirmPlaceFromList')}
                </div>
              )}
              {placesError && (
                <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-4 rounded-xl text-eldergo-navy font-medium">
                  {placesError}
                </div>
              )}

              <p
                className="min-h-[2.75rem] px-1 text-left font-semibold leading-snug text-eldergo-navy"
                style={{ fontSize: `${16 * baseFontSize}px` }}
              >
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
                  setStartFieldErrorKey(null);
                  if (startPoint.trim() && startSuggestions.length > 0) {
                    setShowStartDropdown(true);
                  }
                }}
                onBlur={() => {
                  void tryResolveFieldOnBlur(
                    startPoint,
                    selectedOrigin,
                    setStartPoint,
                    setSelectedOrigin,
                    setRouteOrigin,
                    setResolvingStart,
                    setStartFieldErrorKey
                  );
                }}
                resolving={resolvingStart}
                onSelectSuggestion={handleStartSelect}
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

              <p
                className="min-h-[2.75rem] px-1 text-left font-semibold leading-snug text-eldergo-navy"
                style={{ fontSize: `${16 * baseFontSize}px` }}
              >
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
                  setDestFieldErrorKey(null);
                  if (destination.trim() && destSuggestions.length > 0) {
                    setShowDestDropdown(true);
                  }
                }}
                onBlur={() => {
                  void tryResolveFieldOnBlur(
                    destination,
                    selectedDestination,
                    setDestination,
                    setSelectedDestination,
                    setRouteDestination,
                    setResolvingDest,
                    setDestFieldErrorKey
                  );
                }}
                resolving={resolvingDest}
                onSelectSuggestion={handleDestSelect}
              />

              <button
                type="button"
                onClick={handleSearch}
                disabled={searchDisabled}
                className="w-full rounded-xl bg-eldergo-warning py-4 font-semibold text-white shadow-md transition-colors hover:bg-eldergo-warning-dark disabled:cursor-not-allowed disabled:bg-eldergo-border disabled:text-white/80"
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
