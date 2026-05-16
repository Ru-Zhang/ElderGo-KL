import * as React from 'react';
import { useEffect, useState, type ReactNode } from 'react';
import {
  Accessibility,
  AlertTriangle,
  Check,
  Clock,
  HelpCircle,
  MapPin,
  TrainFront,
} from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { ImageWithFallback } from '../components/common/ImageWithFallback';
import { HoursDisplay } from '../components/common/HoursDisplay';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { getLocationDetail } from '../services/locationsApi';
import {
  getStationGooglePlaceDetail,
  getStationStaticImageUrl,
  placeDetailToSelection,
} from '../services/googlePlaces';
import { formatPlaceDisplayName } from '../utils/placeDisplay';
import { LineBadge } from '../utils/lineBadge';
import { parseHoursSummary } from '../utils/hoursParser';
import { prepareFacilitiesForDisplay } from '../utils/facilityPriority';
import FacilityChips from '../components/common/FacilityChips';

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
  onShowChatbot,
}: StationDetailPageProps) {
  const { fontSize, language, selectedStation, setDestination, setSelectedStation } = useAppContext();
  const [detailLoading, setDetailLoading] = useState(false);
  const [placeLoading, setPlaceLoading] = useState(false);
  const [planRouteLoading, setPlanRouteLoading] = useState(false);
  const [placeError, setPlaceError] = useState<string | null>(null);
  const [showLastTrains, setShowLastTrains] = useState(false);

  useEffect(() => {
    if (!selectedStation?.id) return;
    if (selectedStation.source_list.length > 0) return;

    let cancelled = false;
    setDetailLoading(true);
    getLocationDetail(selectedStation.id)
      .then((detail) => {
        if (!cancelled && detail) {
          setSelectedStation(detail);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPlaceError(t('stationDataUnavailable'));
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedStation?.id, selectedStation?.source_list.length, setSelectedStation, language]);

  const stationImageUrl = selectedStation
    ? getStationStaticImageUrl(selectedStation.name, selectedStation.lat, selectedStation.lon)
    : '/background-elder.png';
  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: string) => getTranslation(language, key as any);

  const status = selectedStation?.accessibility_status ?? 'unknown';
  const facilities = prepareFacilitiesForDisplay(selectedStation?.station_facilities ?? []);
  const address = selectedStation?.station_address ?? null;
  const hours = selectedStation?.station_hours_summary ?? null;
  const parsedHours = parseHoursSummary(hours);
  const facilitySourceUrl = selectedStation?.facility_source_url ?? null;

  // Compact pill style for the accessibility row inside the at-a-glance card.
  // Keeps the "verdict" visible without a dominating standalone banner.
  const accessibilityChip =
    status === 'supported'
      ? {
          bg: 'bg-eldergo-green/15',
          fg: 'text-eldergo-green',
          Icon: Check,
          label: t('accessibilityChipSupported'),
        }
      : status === 'not_supported'
        ? {
            bg: 'bg-red-100',
            fg: 'text-red-700',
            Icon: AlertTriangle,
            label: t('accessibilityChipNotSupported'),
          }
        : {
            bg: 'bg-eldergo-warning-bg',
            fg: 'text-eldergo-warning',
            Icon: HelpCircle,
            label: t('accessibilityChipUnknown'),
          };

  const handleMoreDetails = async () => {
    if (!selectedStation) return;
    setPlaceLoading(true);
    setPlaceError(null);
    try {
      const detail = await getStationGooglePlaceDetail(
        selectedStation.name,
        selectedStation.lat,
        selectedStation.lon,
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

  const handlePlanRoute = async () => {
    if (!selectedStation) return;
    setPlanRouteLoading(true);
    const fallback = {
      displayName: formatPlaceDisplayName(selectedStation.name),
      lat: selectedStation.lat ?? null,
      lon: selectedStation.lon ?? null,
      googlePlaceId: null,
    };
    try {
      const detail = await getStationGooglePlaceDetail(
        selectedStation.name,
        selectedStation.lat,
        selectedStation.lon,
      );
      setDestination(placeDetailToSelection(detail));
    } catch {
      setDestination(fallback);
    } finally {
      setPlanRouteLoading(false);
      onNavigateToPlanning();
    }
  };

  const dataSourcesLine = [
    ...(selectedStation?.source_list ?? []),
    facilitySourceUrl ? 'mrt.com.my' : null,
  ].filter(Boolean) as string[];

  if (!selectedStation) {
    return (
      <div className="min-h-screen relative w-full max-w-full overflow-x-hidden" style={{ fontFamily: 'Poppins' }}>
        <div
          className="fixed inset-0 z-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(/background-elder.png)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
          <div className="absolute inset-0 bg-white/40" />
          <div
            className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
            style={{
              backgroundImage: 'url(/watermark-elder.jpg)',
              opacity: '0.12',
            }}
          />
        </div>
        <div className="relative z-10">
          <TopBar onLogoClick={onNavigateToStation} />
          <main className="pt-20 pb-32 px-4 sm:px-6">
            <div className="mx-auto mt-8 max-w-2xl w-full min-w-0">
              <div className="bg-eldergo-warning-bg border-l-4 border-eldergo-warning p-8 rounded-xl flex items-start gap-4">
                <AlertTriangle
                  size={32 * baseFontSize}
                  strokeWidth={2.5}
                  className="text-eldergo-warning flex-shrink-0"
                />
                <div className="flex-1">
                  <h3
                    className="font-semibold text-eldergo-navy mb-3"
                    style={{ fontSize: `${24 * baseFontSize}px` }}
                  >
                    {t('stationNotFound')}
                  </h3>
                  <p
                    className="text-eldergo-muted mb-6"
                    style={{ fontSize: `${18 * baseFontSize}px` }}
                  >
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
    <div className="min-h-screen relative w-full max-w-full overflow-x-hidden" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: `url(${stationImageUrl})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="absolute inset-0 bg-white/40" />
        <div
          className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12',
          }}
        />
      </div>
      <div className="relative z-10">
        <TopBar onLogoClick={onNavigateToStation} />

        <main className="bg-white pb-32 pt-[72px] w-full min-w-0 overflow-x-hidden">
          {/* Hero */}
          <div className="relative h-80 w-full min-w-0 overflow-hidden">
            <div className="absolute inset-0 bg-black/20" />
            <ImageWithFallback
              src={stationImageUrl}
              alt={`${selectedStation.name} station`}
              className="w-full h-full object-cover"
            />
            <h1
              className="absolute bottom-8 left-4 right-4 sm:left-8 sm:right-8 font-semibold text-white drop-shadow-lg leading-tight break-words hyphens-auto"
              style={{ fontSize: `${36 * baseFontSize}px` }}
            >
              {selectedStation.name}
            </h1>
          </div>

          <div className="mx-auto mt-8 max-w-3xl space-y-6 px-4 sm:px-6 w-full min-w-0 box-border">
            {/* At-a-glance card: Accessibility / Lines / Address / Hours */}
            <div className="space-y-5 rounded-2xl bg-white p-5 shadow-lg sm:p-7 overflow-hidden min-w-0">
              <InfoRow
                Icon={Accessibility}
                label={t('accessibilityStatus')}
                baseFontSize={baseFontSize}
              >
                <span
                  className={`inline-flex items-center gap-2 rounded-full px-3 py-1 font-semibold ${accessibilityChip.bg} ${accessibilityChip.fg}`}
                  style={{ fontSize: `${15 * baseFontSize}px` }}
                >
                  <accessibilityChip.Icon
                    size={16 * baseFontSize}
                    strokeWidth={2.6}
                    aria-hidden
                  />
                  {accessibilityChip.label}
                </span>
              </InfoRow>

              <div className="h-px bg-eldergo-border" />

              <InfoRow
                Icon={TrainFront}
                label={t('routes')}
                baseFontSize={baseFontSize}
              >
                {selectedStation.routes.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedStation.routes.map((r) => (
                      <LineBadge key={r} name={r} baseFontSize={baseFontSize} />
                    ))}
                  </div>
                ) : (
                  <span
                    className="text-eldergo-muted font-medium"
                    style={{ fontSize: `${18 * baseFontSize}px` }}
                  >
                    {t('notYetVerified')}
                  </span>
                )}
              </InfoRow>

              {address && (
                <>
                  <div className="h-px bg-eldergo-border" />
                  <InfoRow
                    Icon={MapPin}
                    label={t('stationAddress')}
                    baseFontSize={baseFontSize}
                  >
                    <span
                      className="text-eldergo-navy font-medium"
                      style={{ fontSize: `${18 * baseFontSize}px`, lineHeight: 1.4 }}
                    >
                      {address}
                    </span>
                  </InfoRow>
                </>
              )}

              {parsedHours && (
                <>
                  <div className="h-px bg-eldergo-border" />
                  <InfoRow Icon={Clock} label={t('stationHours')} baseFontSize={baseFontSize}>
                    <HoursDisplay
                      parsed={parsedHours}
                      baseFontSize={baseFontSize}
                      t={t}
                      language={language}
                      isExpanded={showLastTrains}
                      onToggle={() => setShowLastTrains((v) => !v)}
                    />
                  </InfoRow>
                </>
              )}
            </div>

            {/* Section 3: Station facilities + sources footer */}
            <div className="space-y-5 rounded-2xl bg-white p-5 shadow-lg sm:p-7 overflow-hidden min-w-0">
              <h2
                className="font-semibold text-eldergo-navy"
                style={{ fontSize: `${22 * baseFontSize}px` }}
              >
                {t('stationFacilities')}
              </h2>
              {facilities.length > 0 ? (
                <FacilityChips items={facilities} language={language} baseFontSize={baseFontSize} />
              ) : (
                <p
                  className="text-eldergo-muted"
                  style={{ fontSize: `${16 * baseFontSize}px` }}
                >
                  {t('facilitiesUnavailable')}
                </p>
              )}

              {dataSourcesLine.length > 0 && (
                <div
                  className="pt-4 border-t border-eldergo-border text-eldergo-muted flex flex-wrap items-center gap-2"
                  style={{ fontSize: `${13 * baseFontSize}px` }}
                >
                  <span className="font-medium">{t('dataSourcesLabel')}:</span>
                  {dataSourcesLine.map((source, idx) => {
                    const isLink = source === 'mrt.com.my' && facilitySourceUrl;
                    return (
                      <span key={`${source}-${idx}`} className="inline-flex items-center gap-2">
                        {idx > 0 && <span className="text-eldergo-muted">·</span>}
                        {isLink ? (
                          <a
                            href={facilitySourceUrl ?? undefined}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-eldergo-blue underline font-medium"
                          >
                            {source}
                          </a>
                        ) : (
                          <span>{source}</span>
                        )}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Section 4: Action buttons.
                Two-tier hierarchy mirrored from the brand UI preview —
                primary action filled blue, secondary action white with a
                blue outline so users can clearly distinguish them. */}
            <div className="space-y-3">
              <button
                type="button"
                onClick={() => void handlePlanRoute()}
                disabled={planRouteLoading}
                aria-label={t('planRouteToStation')}
                className="w-full bg-eldergo-blue hover:bg-eldergo-blue-dark disabled:bg-eldergo-muted text-white font-semibold py-6 rounded-2xl transition-colors shadow-lg min-h-[80px] flex items-center justify-center text-center leading-snug px-4"
                style={{ fontSize: `${22 * baseFontSize}px` }}
              >
                {planRouteLoading ? t('loadingPlaceDetails') : t('planRouteToStation')}
              </button>

              <button
                onClick={handleMoreDetails}
                disabled={placeLoading}
                className="w-full bg-white border-2 border-eldergo-blue text-eldergo-blue-dark hover:bg-eldergo-blue/5 active:bg-eldergo-blue/10 disabled:bg-eldergo-bg disabled:border-eldergo-border disabled:text-eldergo-muted font-semibold py-6 rounded-2xl transition-colors shadow-sm min-h-[80px] flex items-center justify-center gap-3"
                style={{ fontSize: `${22 * baseFontSize}px` }}
              >
                <MapPin size={26 * baseFontSize} strokeWidth={2.4} />
                {placeLoading ? t('loadingPlaceDetails') : t('moreDetails')}
              </button>

              {placeError && (
                <p
                  className="bg-white rounded-2xl shadow-md p-5 text-eldergo-warning-dark font-medium border border-eldergo-warning-bg"
                  style={{ fontSize: `${18 * baseFontSize}px` }}
                >
                  {placeError}
                </p>
              )}
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

interface InfoRowProps {
  Icon: typeof Check;
  label: string;
  baseFontSize: number;
  children: ReactNode;
}

function InfoRow({ Icon, label, baseFontSize, children }: InfoRowProps) {
  return (
    <div className="flex gap-4 items-start">
      <div
        className="flex-shrink-0 rounded-full bg-eldergo-blue/10 flex items-center justify-center"
        style={{
          width: 40 * baseFontSize,
          height: 40 * baseFontSize,
        }}
      >
        <Icon
          className="text-eldergo-blue"
          size={22 * baseFontSize}
          strokeWidth={2.4}
        />
      </div>
      <div className="flex-1 min-w-0 pt-1">
        <p
          className="font-semibold text-eldergo-muted mb-1.5 uppercase tracking-wide"
          style={{ fontSize: `${12 * baseFontSize}px`, letterSpacing: '0.06em' }}
        >
          {label}
        </p>
        {children}
      </div>
    </div>
  );
}
