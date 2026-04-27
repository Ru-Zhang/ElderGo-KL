import { useState } from 'react';
import { Check, AlertTriangle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { ImageWithFallback } from '../components/common/ImageWithFallback';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { getStationGooglePlaceDetail, getStationStaticImageUrl } from '../services/googlePlaces';

interface StationDetailPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

export default function StationDetailPage({
  onNavigateToPlanning,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot
}: StationDetailPageProps) {
  const { fontSize, language, selectedStation } = useAppContext();
  const [placeLoading, setPlaceLoading] = useState(false);
  const [placeError, setPlaceError] = useState<string | null>(null);
  const stationImageUrl = selectedStation
    ? getStationStaticImageUrl(selectedStation.name, selectedStation.lat, selectedStation.lon)
    : '/background-elder.png';
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);
  const accessibilityLabel = () => {
    if (selectedStation?.accessibility_status === 'supported') return 'supported';
    if (selectedStation?.accessibility_status === 'not_supported') return 'not supported';
    return 'unknown';
  };
  const handleMoreDetails = async () => {
    if (!selectedStation) return;
    setPlaceLoading(true);
    setPlaceError(null);
    try {
      const detail = await getStationGooglePlaceDetail(
        selectedStation.name,
        selectedStation.lat,
        selectedStation.lon
      );
      const mapsUrl = new URL('https://www.google.com/maps/search/');
      mapsUrl.searchParams.set('api', '1');
      mapsUrl.searchParams.set('query', detail.name || selectedStation.name);
      mapsUrl.searchParams.set('query_place_id', detail.google_place_id);
      window.open(mapsUrl.toString(), '_blank', 'noopener,noreferrer');
    } catch {
      setPlaceError(t('googlePlacesUnavailable'));
    } finally {
      setPlaceLoading(false);
    }
  };

  if (!selectedStation) {
    return (
      <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
        <div
          className="fixed inset-0 z-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(/background-elder.png)',
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
          <TopBar onLogoClick={onNavigateToStation} />

          <main className="pt-20 pb-32 px-6">
            <div className="max-w-2xl mx-auto mt-8">
              <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-8 rounded-xl flex items-start gap-4">
                <AlertTriangle size={32 * baseFontSize} strokeWidth={2.5} className="text-eldergo-warning flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-eldergo-navy mb-3" style={{ fontSize: `${24 * baseFontSize}px` }}>
                    {t('stationNotFound')}
                  </h3>
                  <p className="text-eldergo-muted mb-6" style={{ fontSize: `${18 * baseFontSize}px` }}>
                    {t('stationNotFoundMessage')}
                  </p>
                  <button
                    onClick={onNavigateToStation}
                    className="bg-eldergo-blue hover:bg-eldergo-blue-dark text-white font-semibold py-4 px-6 rounded-xl transition-colors shadow-md"
                    style={{ fontSize: `${18 * baseFontSize}px` }}
                  >
                    {t('backToStations')}
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
          backgroundImage: `url(${stationImageUrl})`,
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
      <TopBar onLogoClick={onNavigateToStation} />

      <main className="pt-[72px] pb-32 bg-white">
        <div className="relative h-80">
          <div className="absolute inset-0 bg-black/20" />
          <ImageWithFallback
            src={stationImageUrl}
            alt={`${selectedStation.name} station`}
            className="w-full h-full object-cover"
          />
          <h1 className="absolute bottom-8 left-8 font-bold text-white drop-shadow-lg" style={{ fontSize: `${36 * baseFontSize}px` }}>
            {selectedStation.name}
          </h1>
        </div>

        <div className="max-w-3xl mx-auto px-6 mt-8 space-y-6">
          <div className="bg-white rounded-2xl shadow-lg p-8 space-y-6">
            <div className="flex items-center gap-5 min-h-[64px]">
              <div className="w-12 h-12 bg-eldergo-blue/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Check size={28 * baseFontSize} strokeWidth={3} className="text-eldergo-blue" />
              </div>
              <span className="font-medium text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('routes')}: <span className="font-semibold text-eldergo-blue">
                  {selectedStation.routes.length ? selectedStation.routes.join(', ') : t('notYetVerified')}
                </span>
              </span>
            </div>

            <div className="h-px bg-gray-200" />

            <div className="flex items-center gap-5 min-h-[64px]">
              <div className="w-12 h-12 bg-eldergo-green/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Check size={28 * baseFontSize} strokeWidth={3} className="text-eldergo-green" />
              </div>
              <span className="font-medium text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('accessibilityStatus')}: <span className="font-semibold text-eldergo-green">
                  {accessibilityLabel()}
                </span>
              </span>
            </div>

            <div className="h-px bg-gray-200" />

            <div className="flex items-center gap-5 min-h-[64px]">
              <div className="w-12 h-12 bg-eldergo-warning/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Check size={28 * baseFontSize} strokeWidth={3} className="text-eldergo-warning" />
              </div>
              <span className="font-medium text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                Details: <span className="font-semibold text-eldergo-warning">
                  {selectedStation.known_facilities.length ? selectedStation.known_facilities.join(', ') : t('notYetVerified')}
                </span>
              </span>
            </div>

            <div className="h-px bg-gray-200" />

            <div className="flex items-center gap-5 min-h-[64px]">
              <div className="w-12 h-12 bg-eldergo-warning/20 rounded-full flex items-center justify-center flex-shrink-0">
                <AlertTriangle size={28 * baseFontSize} strokeWidth={3} className="text-eldergo-warning" />
              </div>
              <span className="font-medium text-eldergo-navy" style={{ fontSize: `${22 * baseFontSize}px` }}>
                {t('dataSource')}: <span className="font-semibold text-eldergo-warning">
                  {selectedStation.source_list.length ? selectedStation.source_list.join(', ') : t('notYetVerified')}
                </span>
              </span>
            </div>
          </div>

          <button
            onClick={handleMoreDetails}
            disabled={placeLoading}
            className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark disabled:bg-gray-400 text-white font-semibold py-6 rounded-2xl transition-colors shadow-lg min-h-[80px]"
            style={{ fontSize: `${24 * baseFontSize}px` }}
          >
            {placeLoading ? t('loadingPlaceDetails') : t('moreDetails')}
          </button>

          {placeError && (
            <p className="bg-white rounded-2xl shadow-lg p-6 text-eldergo-warning font-medium" style={{ fontSize: `${18 * baseFontSize}px` }}>
              {placeError}
            </p>
          )}
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
