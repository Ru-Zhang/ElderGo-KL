import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { LocationDetail, PlaceSelection } from '../types/locations';
import { TravelPreferences } from '../types/preferences';
import { RecommendedRoute } from '../types/routes';
import { FontSizeMode, LanguageCode, UISettings } from '../types/settings';
import { getOrCreateDeviceId } from '../utils/deviceId';
import {
  createAnonymousUser,
  getTravelPreferences,
  getUISettings,
  updateTravelPreferences,
  updateUISettings
} from '../services/usersApi';

const LOCAL_SETTINGS_KEY = 'eldergo_ui_settings';
const LOCAL_PREFERENCES_KEY = 'eldergo_travel_preferences';

interface AppContextType {
  anonymousUserId: string | null;
  language: LanguageCode;
  fontSize: FontSizeMode;
  onboardingCompleted: boolean;
  preferences: TravelPreferences;
  origin: PlaceSelection | null;
  destination: PlaceSelection | null;
  departureTime: string;
  currentRoute: RecommendedRoute | null;
  routeLoading: boolean;
  routeError: string | null;
  selectedStation: LocationDetail | null;
  toggleLanguage: () => void;
  toggleFontSize: () => void;
  setOnboardingCompleted: (completed: boolean) => void;
  updatePreferences: (prefs: TravelPreferences) => void;
  clearPreferences: () => void;
  setOrigin: (origin: PlaceSelection | null) => void;
  setDestination: (destination: PlaceSelection | null) => void;
  setDepartureTime: (departureTime: string) => void;
  setCurrentRoute: (route: RecommendedRoute | null) => void;
  setRouteLoading: (loading: boolean) => void;
  setRouteError: (error: string | null) => void;
  setSelectedStation: (station: LocationDetail | null) => void;
}

const defaultPreferences: TravelPreferences = {
  accessibilityFirst: false,
  leastWalk: false,
  fewestTransfers: false
};

const defaultSettings: UISettings = {
  language: 'EN',
  fontSize: 'standard',
  onboardingCompleted: false
};

function loadLocalSettings(): UISettings {
  try {
    const raw = localStorage.getItem(LOCAL_SETTINGS_KEY);
    return raw ? { ...defaultSettings, ...JSON.parse(raw) } : defaultSettings;
  } catch {
    return defaultSettings;
  }
}

function loadLocalPreferences(): TravelPreferences {
  try {
    const raw = localStorage.getItem(LOCAL_PREFERENCES_KEY);
    return raw ? { ...defaultPreferences, ...JSON.parse(raw) } : defaultPreferences;
  } catch {
    return defaultPreferences;
  }
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [anonymousUserId, setAnonymousUserId] = useState<string | null>(null);
  const [settings, setSettings] = useState<UISettings>(loadLocalSettings);
  const [preferences, setPreferences] = useState<TravelPreferences>(loadLocalPreferences);
  const [origin, setOrigin] = useState<PlaceSelection | null>(null);
  const [destination, setDestination] = useState<PlaceSelection | null>(null);
  const [departureTime, setDepartureTime] = useState('now');
  const [currentRoute, setCurrentRoute] = useState<RecommendedRoute | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [selectedStation, setSelectedStation] = useState<LocationDetail | null>(null);
  // Guard flags prevent late remote restore responses from overwriting user
  // interactions that happen immediately after app startup.
  const settingsChangedDuringRestoreRef = useRef(false);
  const preferencesChangedDuringRestoreRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function restoreUserCache() {
      try {
        const deviceId = getOrCreateDeviceId();
        const restoredAnonymousUserId = await createAnonymousUser(deviceId);
        if (cancelled) return;

        setAnonymousUserId(restoredAnonymousUserId);
        // Fetch both payloads together to shorten startup sync time.
        const [remoteSettings, remotePreferences] = await Promise.all([
          getUISettings(restoredAnonymousUserId),
          getTravelPreferences(restoredAnonymousUserId)
        ]);
        if (cancelled) return;

        if (!settingsChangedDuringRestoreRef.current) {
          setSettings(remoteSettings);
          localStorage.setItem(LOCAL_SETTINGS_KEY, JSON.stringify(remoteSettings));
        }
        if (!preferencesChangedDuringRestoreRef.current) {
          setPreferences(remotePreferences);
          localStorage.setItem(LOCAL_PREFERENCES_KEY, JSON.stringify(remotePreferences));
        }
      } catch {
        // Local fallback keeps the prototype usable before backend setup.
      }
    }

    restoreUserCache();

    return () => {
      cancelled = true;
    };
  }, []);

  const persistSettings = (nextSettings: UISettings) => {
    // Local cache is updated first so UI feels instant even if network sync fails.
    settingsChangedDuringRestoreRef.current = true;
    setSettings(nextSettings);
    localStorage.setItem(LOCAL_SETTINGS_KEY, JSON.stringify(nextSettings));
    if (anonymousUserId) {
      updateUISettings(anonymousUserId, nextSettings).catch(() => undefined);
    }
  };

  const toggleLanguage = () => {
    const nextLanguage = settings.language === 'EN' ? 'BM' : 'EN';
    persistSettings({
      ...settings,
      language: nextLanguage
    });
  };

  const toggleFontSize = () => {
    const nextFontSize =
      settings.fontSize === 'standard'
        ? 'large'
        : settings.fontSize === 'large'
          ? 'extra_large'
          : 'standard';

    persistSettings({
      ...settings,
      fontSize: nextFontSize
    });
  };

  const setOnboardingCompleted = (completed: boolean) => {
    persistSettings({
      ...settings,
      onboardingCompleted: completed
    });
  };

  const updatePreferencesLocal = (prefs: TravelPreferences) => {
    // Mirror settings persistence strategy for preferences.
    preferencesChangedDuringRestoreRef.current = true;
    setPreferences(prefs);
    localStorage.setItem(LOCAL_PREFERENCES_KEY, JSON.stringify(prefs));
    if (anonymousUserId) {
      updateTravelPreferences(anonymousUserId, prefs).catch(() => undefined);
    }
  };

  const clearPreferences = () => {
    updatePreferencesLocal(defaultPreferences);
  };

  return (
    <AppContext.Provider value={{
      anonymousUserId,
      language: settings.language,
      fontSize: settings.fontSize,
      onboardingCompleted: settings.onboardingCompleted,
      preferences,
      origin,
      destination,
      departureTime,
      currentRoute,
      routeLoading,
      routeError,
      selectedStation,
      toggleLanguage,
      toggleFontSize,
      setOnboardingCompleted,
      updatePreferences: updatePreferencesLocal,
      clearPreferences,
      setOrigin,
      setDestination,
      setDepartureTime,
      setCurrentRoute,
      setRouteLoading,
      setRouteError,
      setSelectedStation
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
