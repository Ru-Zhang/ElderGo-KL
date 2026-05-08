import * as React from 'react';
import { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Accessibility,
  ChevronRight,
  HelpCircle,
  Search,
} from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { getLocationDetail, getPopularLocations, searchLocations } from '../services/locationsApi';
import { LocationSummary, AccessibilityStatus } from '../types/locations';
import { getTranslation } from '../i18n/translations';
import { LineBadge } from '../utils/lineBadge';

interface StationsHomePageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStationDetail: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

function canonicalStationName(name: string): string {
  return name
    .trim()
    .replace(/\s*[-–—]?\s*REDONE$/i, '')
    .replace(/\s+/g, ' ')
    .replace(/([A-Z])\s+(\d)/gi, '$1$2')
    .toUpperCase();
}

function dedupeLocations(locations: LocationSummary[]): LocationSummary[] {
  const seenIds = new Set<string>();
  const seenStationNames = new Set<string>();
  const deduped: LocationSummary[] = [];

  for (const location of locations) {
    if (seenIds.has(location.id)) {
      continue;
    }
    seenIds.add(location.id);

    // Keep one card per canonical station name to avoid duplicate entries
    // coming from multiple source systems.
    if (location.type === 'rail_station') {
      const stationKey = canonicalStationName(location.name);
      if (seenStationNames.has(stationKey)) {
        continue;
      }
      seenStationNames.add(stationKey);
    }

    deduped.push(location);
  }

  return deduped;
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

  // Map status to a small icon badge that replaces verbose status text on cards.
  const accessibilityChip = (status: AccessibilityStatus) => {
    if (status === 'supported') {
      return {
        Icon: Accessibility,
        bg: 'bg-eldergo-green/15',
        fg: 'text-eldergo-green',
        srLabel: t('supportedAccessibility'),
      };
    }
    if (status === 'not_supported') {
      return {
        Icon: AlertTriangle,
        bg: 'bg-red-100',
        fg: 'text-red-600',
        srLabel: t('notSupportedAccessibility'),
      };
    }
    return {
      Icon: HelpCircle,
      bg: 'bg-eldergo-warning-bg',
      fg: 'text-eldergo-warning',
      srLabel: t('unknownAccessibility'),
    };
  };

  const [searchQuery, setSearchQuery] = useState('');
  const [popularStations, setPopularStations] = useState<LocationSummary[]>([]);
  const [searchResults, setSearchResults] = useState<LocationSummary[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Re-fetch on language change so fallback/error messages stay localized.
    getPopularLocations()
      .then((locations) => setPopularStations(dedupeLocations(locations)))
      .catch(() => setError(t('stationDatabaseNotReady')));
  }, [language]);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }

    // Mark searched state only for non-empty input to control empty-state UI.
    setHasSearched(true);
    try {
      const locations = await searchLocations(query);
      setSearchResults(dedupeLocations(locations));
      setError(null);
    } catch {
      setSearchResults([]);
      setError(t('stationDatabaseNotReady'));
    }
  };

  const handleStationClick = async (location: LocationSummary) => {
    try {
      // Load full detail payload before navigation so destination page can render
      // immediately without another blocking fetch.
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
    <div className="min-h-screen relative w-full max-w-full overflow-x-hidden" style={{ fontFamily: 'Poppins' }}>
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

      <main className="pt-20 pb-32 px-4 sm:px-6 w-full min-w-0 box-border">
        <div className="max-w-2xl mx-auto mt-8 w-full min-w-0">
          {/* Search bar — pill-shaped to match the brand UI preview */}
          <div className="relative mb-10">
            <Search
              className="absolute left-6 top-1/2 -translate-y-1/2 text-eldergo-muted"
              size={26 * baseFontSize}
              strokeWidth={2.4}
            />
            <input
              type="text"
              placeholder={t('searchStationPlaceholder')}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-16 pr-6 py-5 bg-white border border-eldergo-border rounded-full font-medium text-eldergo-navy placeholder:text-eldergo-muted focus:outline-none focus:border-eldergo-blue focus:ring-2 focus:ring-eldergo-blue/20 shadow-sm transition-shadow"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            />
          </div>

          {(error || (hasSearched && searchResults.length === 0)) && (
            <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-6 rounded-xl mb-6 flex items-center gap-4">
              <AlertCircle size={28 * baseFontSize} strokeWidth={2.5} className="text-eldergo-warning flex-shrink-0" />
              <div>
                <p className="font-semibold text-eldergo-navy mb-1" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {error ? t('stationDataUnavailable') : t('noStationsFound')}
                </p>
                <p className="text-eldergo-muted" style={{ fontSize: `${18 * baseFontSize}px` }}>
                  {error || t('tryDifferentKeyword')}
                </p>
              </div>
            </div>
          )}

          {shownLocations.length > 0 && (
            <>
              <h2
                className="font-semibold text-eldergo-navy mb-6 leading-tight"
                style={{ fontSize: `${24 * baseFontSize}px` }}
              >
                {hasSearched ? `${t('searchResults')} (${searchResults.length})` : t('popularStations')}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full min-w-0">
                {shownLocations.map((location) => {
                  const chip = accessibilityChip(location.accessibility_status);
                  const routes = location.routes ?? [];
                  const visibleRoutes = routes.slice(0, 3);
                  const overflow = routes.length - visibleRoutes.length;
                  return (
                    <button
                      key={location.id}
                      onClick={() => handleStationClick(location)}
                      // Brand-aligned card: white surface, single-pixel border in
                      // brand `eldergo-border`, soft shadow that deepens on hover
                      // — no heavy outlines so the card reads as a calm tile
                      // rather than a button shape.
                      className="bg-white border border-eldergo-border rounded-2xl shadow-md hover:shadow-xl hover:border-eldergo-blue/40 hover:-translate-y-0.5 transition-all flex flex-col text-left overflow-hidden min-h-[170px] group min-w-0 w-full max-w-full"
                    >
                      <div className="p-5 flex-1 flex flex-col gap-3">
                        <div className="flex items-start justify-between gap-2 min-w-0">
                          <span
                            className="font-semibold text-eldergo-navy leading-tight min-w-0 break-words"
                            style={{ fontSize: `${20 * baseFontSize}px` }}
                          >
                            {location.name}
                          </span>
                          <span
                            className={`flex-shrink-0 rounded-full flex items-center justify-center ${chip.bg}`}
                            title={chip.srLabel}
                            aria-label={chip.srLabel}
                            style={{ width: 36 * baseFontSize, height: 36 * baseFontSize }}
                          >
                            <chip.Icon
                              size={18 * baseFontSize}
                              strokeWidth={2.4}
                              className={chip.fg}
                            />
                          </span>
                        </div>

                        {visibleRoutes.length > 0 ? (
                          <div className="flex flex-wrap items-center gap-1.5">
                            {visibleRoutes.map((r) => (
                              <LineBadge key={r} name={r} baseFontSize={baseFontSize} />
                            ))}
                            {overflow > 0 && (
                              <span
                                className="text-eldergo-muted font-medium"
                                style={{ fontSize: `${13 * baseFontSize}px` }}
                              >
                                +{overflow}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span
                            className="text-eldergo-muted"
                            style={{ fontSize: `${13 * baseFontSize}px` }}
                          >
                            {t('notYetVerified')}
                          </span>
                        )}
                      </div>

                      <div className="px-5 py-3 border-t border-eldergo-border flex items-center justify-end gap-1 text-eldergo-blue group-hover:text-eldergo-blue-dark transition-colors">
                        <span
                          className="font-semibold"
                          style={{ fontSize: `${14 * baseFontSize}px` }}
                        >
                          {t('viewDetails')}
                        </span>
                        <ChevronRight
                          size={18 * baseFontSize}
                          strokeWidth={2.6}
                        />
                      </div>
                    </button>
                  );
                })}
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
