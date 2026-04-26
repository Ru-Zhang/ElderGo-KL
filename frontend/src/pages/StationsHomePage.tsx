import { useEffect, useState } from 'react';
import { Search, ChevronRight, AlertCircle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { getLocationDetail, getPopularLocations, searchLocations } from '../services/locationsApi';
import { LocationSummary } from '../types/locations';
import { getTranslation } from '../i18n/translations';

interface StationsHomePageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStationDetail: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function StationsHomePage({
  onNavigateToPlanning,
  onNavigateToStationDetail,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot
}: StationsHomePageProps) {
  const { fontSize, language, setSelectedStation } = useAppContext();
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const [searchQuery, setSearchQuery] = useState('');
  const [popularStations, setPopularStations] = useState<LocationSummary[]>([]);
  const [searchResults, setSearchResults] = useState<LocationSummary[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPopularLocations()
      .then(setPopularStations)
      .catch(() => setError(t('stationDatabaseNotReady')));
  }, [language]);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }

    setHasSearched(true);
    try {
      setSearchResults(await searchLocations(query));
      setError(null);
    } catch {
      setSearchResults([]);
      setError(t('stationDatabaseNotReady'));
    }
  };

  const handleStationClick = async (location: LocationSummary) => {
    try {
      const detail = await getLocationDetail(location.id);
      if (detail) {
        setSelectedStation(detail);
        onNavigateToStationDetail();
      }
    } catch {
      setError(t('stationDatabaseNotReady'));
    }
  };

  const shownLocations = hasSearched ? searchResults : popularStations;

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
        <div className="absolute inset-0 bg-white/45" />
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
          <div className="relative mb-10">
            <Search
              className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400"
              size={28 * baseFontSize}
              strokeWidth={2.5}
            />
            <input
              type="text"
              placeholder={t('searchStationPlaceholder')}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-16 pr-6 py-5 bg-white border-2 border-gray-300 rounded-xl font-medium text-[#1E3A5F] placeholder:text-gray-400 focus:outline-none focus:border-[#4A90E2] shadow-md"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            />
          </div>

          {(error || (hasSearched && searchResults.length === 0)) && (
            <div className="bg-[#FFE5B4] border-l-4 border-[#E67E22] p-6 rounded-xl mb-6 flex items-center gap-4">
              <AlertCircle size={28 * baseFontSize} strokeWidth={2.5} className="text-[#E67E22] flex-shrink-0" />
              <div>
                <p className="font-semibold text-[#1E3A5F] mb-1" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {error ? t('stationDataUnavailable') : t('noStationsFound')}
                </p>
                <p className="text-gray-700" style={{ fontSize: `${18 * baseFontSize}px` }}>
                  {error || t('tryDifferentKeyword')}
                </p>
              </div>
            </div>
          )}

          {shownLocations.length > 0 && (
            <>
              <h2 className="font-semibold text-[#1E3A5F] mb-6" style={{ fontSize: `${24 * baseFontSize}px` }}>
                {hasSearched ? `${t('searchResults')} (${searchResults.length})` : t('popularStations')}
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {shownLocations.map((location) => (
                  <button
                    key={location.id}
                    onClick={() => handleStationClick(location)}
                    className="bg-[#F5F7FA] border-2 border-gray-300 p-6 rounded-2xl shadow-sm hover:border-[#4A90E2] hover:shadow-md transition-all flex flex-col items-start gap-3 min-h-[140px]"
                  >
                    <span className="font-semibold text-[#1E3A5F] text-left" style={{ fontSize: `${20 * baseFontSize}px` }}>
                      {location.name}
                    </span>
                    <span className="text-gray-600 text-left" style={{ fontSize: `${14 * baseFontSize}px` }}>
                      {t(location.accessibility_status === 'unknown' ? 'unknownAccessibility' : 'verifiedAccessibility')}
                    </span>
                    <ChevronRight size={24 * baseFontSize} strokeWidth={2.5} className="text-gray-400 ml-auto" />
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </main>

        <BottomNav
          activeTab="station"
          onChatbotClick={onShowChatbot}
          onStationClick={() => {}}
          onHelpClick={onNavigateToHelp}
          onPlanningClick={onNavigateToPlanning}
          onPreferenceClick={onNavigateToPreference}
        />
      </div>
    </div>
  );
}
