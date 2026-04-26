import { createContext, useContext, useState, ReactNode } from 'react';

interface PreferencesType {
  accessibilityFirst: boolean;
  leastWalk: boolean;
  fewestTransfers: boolean;
}

export interface StationData {
  id: string;
  name: string;
  wheelchairAccessible: boolean;
  elevatorAvailable: boolean;
  ticketCounter: boolean;
  operatingHours: string;
  imageUrl?: string;
}

interface AppContextType {
  language: 'EN' | 'BM';
  fontSize: 'normal' | 'large';
  preferences: PreferencesType;
  selectedStation: StationData | null;
  toggleLanguage: () => void;
  toggleFontSize: () => void;
  updatePreferences: (prefs: PreferencesType) => void;
  clearPreferences: () => void;
  setSelectedStation: (station: StationData | null) => void;
}

const defaultPreferences: PreferencesType = {
  accessibilityFirst: false,
  leastWalk: false,
  fewestTransfers: false
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<'EN' | 'BM'>('EN');
  const [fontSize, setFontSize] = useState<'normal' | 'large'>('normal');
  const [preferences, setPreferences] = useState<PreferencesType>(defaultPreferences);
  const [selectedStation, setSelectedStation] = useState<StationData | null>(null);

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'EN' ? 'BM' : 'EN');
  };

  const toggleFontSize = () => {
    setFontSize(prev => prev === 'normal' ? 'large' : 'normal');
  };

  const updatePreferences = (prefs: PreferencesType) => {
    setPreferences(prefs);
  };

  const clearPreferences = () => {
    setPreferences(defaultPreferences);
  };

  return (
    <AppContext.Provider value={{
      language,
      fontSize,
      preferences,
      selectedStation,
      toggleLanguage,
      toggleFontSize,
      updatePreferences,
      clearPreferences,
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
