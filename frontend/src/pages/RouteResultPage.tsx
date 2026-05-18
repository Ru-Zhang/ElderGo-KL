import { useEffect, useState, useRef } from 'react';
import { Download, Share2, Train, MapPin, Footprints, ChevronLeft, ChevronRight, ArrowDown, Navigation, Loader2, ArrowRightLeft, Armchair, Users, AlertCircle } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { StationDetailModal } from '../components/common/StationDetailModal';
import { ImageWithFallback } from '../components/common/ImageWithFallback';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { DestinationWeather, getDestinationWeather } from '../services/weatherApi';
import { getStationStaticImageUrl } from '../services/googlePlaces';
import {
  CANONICAL_KLCC_MONASH_ROUTE_KEY,
  isCuratedCorridorRoute,
} from '../utils/curatedRouteImages';
import { fetchRouteStationImageMap, type RouteStationImage } from '../services/routeStationImages';
import GoogleMapsInstallModal from '../components/common/GoogleMapsInstallModal';
import RouteLoadingPanel from '../components/route/RouteLoadingPanel';
import RouteRankingInsight from '../components/route/RouteRankingInsight';
import RouteResultSkeleton from '../components/route/RouteResultSkeleton';
import RouteUnavailableView from '../components/route/RouteUnavailableView';
import RouteWeatherCard from '../components/route/RouteWeatherCard';
import { resolveStationDetailByName } from '../services/resolveStationDetail';
import {
  buildRouteKey,
  getCustomRouteStepImages,
  getCustomStationImages,
  resolveRouteImageUrl,
} from '../utils/routeStationImages';
import type { LocationDetail } from '../types/locations';
import { extractStationNameFromInstruction, cleanStationQuery } from '../utils/stationName';
import {
  getSeatAvailabilityLevel,
  getSeatProbabilityForRouteStep,
  getTravelDateForSeatLookup,
  type SeatAvailabilityLevel,
} from '../utils/seatProbability';
import { getElderHighlightFacilities, getFacilityTier } from '../utils/facilityPriority';
import { pickFacilityIcon } from '../utils/facilityIcons';
import { translateFacility } from '../utils/dataI18n';
import {
  attemptOpenGoogleMaps,
  buildMapsDirectionsUrl,
  openGoogleMapsStore,
} from '../utils/googleMapsNavigation';
import { formatDepartureContextLabel, resolveDepartureDate } from '../utils/departureTime';
import { formatTransitStepTitle } from '../utils/transitModeLabel';

interface RouteResultPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToPlanTime: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
  initialViewMode?: 'text' | 'map';
}

const BRAND_COLORS = {
  blue: '#4A90E2',
  green: '#6BBF59',
  navy: '#1E3A5F',
  warning: '#E67E22',
  bg: '#F5F7FA',
  white: '#FFFFFF',
  border: '#ECEFF3',
  muted: '#66758A',
  body: '#334155'
};

const GOOGLE_MAPS_EMBED_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || import.meta.env.VITE_GOOGLE_MAPS_BROWSER_KEY;
export default function RouteResultPage({
  onNavigateToPlanning,
  onNavigateToPlanTime,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot,
  initialViewMode = 'text'
}: RouteResultPageProps) {
  const [viewMode, setViewMode] = useState<'text' | 'map'>(initialViewMode);
  const [currentStep, setCurrentStep] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const loadedStationKeysRef = useRef<Set<string>>(new Set());
  const {
    currentRoute,
    departureTime,
    origin,
    destination,
    fontSize,
    routeError,
    routeErrorCode,
    routeLoading,
    language,
  } = useAppContext();
  const [shareMenuOpen, setShareMenuOpen] = useState(false);
  const [actionHint, setActionHint] = useState<string | null>(null);
  const [showMapsInstallModal, setShowMapsInstallModal] = useState(false);
  const [weather, setWeather] = useState<DestinationWeather | null>(null);
  const [weatherStatus, setWeatherStatus] = useState<'idle' | 'loading' | 'ready' | 'unavailable'>('idle');
  const [stationModalName, setStationModalName] = useState<string | null>(null);
  const [stepStationDetails, setStepStationDetails] = useState<Record<string, LocationDetail | null>>({});
  const [routeImageMap, setRouteImageMap] = useState<Record<string, RouteStationImage[]>>({});
  const [stepImageIndex, setStepImageIndex] = useState(0);
  const t = (key: string) => getTranslation(language, key as any);
  const travelDateForSeatLookup = getTravelDateForSeatLookup();

  useEffect(() => {
    setViewMode(initialViewMode);
  }, [initialViewMode]);

  const toLocationLabel = (value?: string | null) => {
    if (!value) return '';
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

  const removeBracketContent = (value: string) =>
    value
      .replace(/\s*\([^)]*\)\s*/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();

  const normalizeStepTitle = (
    instruction: string,
    stepType: string,
    fromStation?: string | null,
    toStation?: string | null,
    isLastStep?: boolean,
    destinationName?: string | null,
    appendStationSuffix?: boolean,
    transitLine?: string | null,
    transitVehicleType?: string | null,
    transitHeadsign?: string | null,
  ) => {
    const shortFrom = removeBracketContent(toLocationLabel(fromStation));
    const shortTo = removeBracketContent(toLocationLabel(toStation));
    const shortDestination = removeBracketContent(toLocationLabel(destinationName));
    const cleanedInstruction = removeBracketContent(instruction);
    const actionWalkTo = t('routeActionWalkTo');
    const actionArriveAt = t('routeActionArriveAt');
    const actionFrom = t('routeActionFrom');
    const actionTo = t('routeActionTo');
    const stationSuffix = appendStationSuffix ? ` ${t('routeStationSuffix')}` : '';

    // Keep the last step consistent with the selected destination label.
    if (isLastStep && shortDestination) {
      if (/^arrive at /i.test(cleanedInstruction)) {
        return `${actionArriveAt} ${shortDestination}.`;
      }
      if (/^walk to /i.test(cleanedInstruction)) {
        return `${actionWalkTo} ${shortDestination}`;
      }
    }

    if (stepType === 'transit' && shortFrom && shortTo) {
      return formatTransitStepTitle(
        language,
        shortFrom,
        shortTo,
        transitLine,
        transitVehicleType,
        transitHeadsign,
      );
    }

    const walkToMatch = cleanedInstruction.match(/^(Walk to )(.+)$/i);
    if (walkToMatch) {
      return `${actionWalkTo} ${removeBracketContent(toLocationLabel(walkToMatch[2]))}${stationSuffix}`;
    }

    const arriveAtMatch = cleanedInstruction.match(/^(Arrive at )(.+?)(\.)?$/i);
    if (arriveAtMatch) {
      return `${actionArriveAt} ${removeBracketContent(toLocationLabel(arriveAtMatch[2]))}${arriveAtMatch[3] || ''}`;
    }

    return cleanedInstruction.replace(/([A-Za-z0-9][^,]*),\s[^.]+/g, (match, firstPart) => {
      if (/^\d+$/.test(firstPart.trim())) return match;
      return firstPart.trim();
    });
  };

  const localizeAccessibilityMessage = (message?: string | null) => {
    if (!message) return t('routeAccessibilityFallback');
    const normalized = message.trim().toLowerCase();
    if (normalized === 'unknown / not yet verified') return t('unknownAccessibility');
    if (normalized === 'verified accessibility data available') return t('verifiedAccessibility');
    if (normalized === 'accessibility annotation will be added from imported station and accessibility data.') {
      return t('routeAccessibilityFallback');
    }
    return message;
  };

  const routeSteps = currentRoute?.steps.map((step, index, allSteps) => {
    // Pick the most relevant station name for the "view station details"
    // popup. For transit segments we want the station you're heading to;
    // for walking segments the destination station (if it's a station)
    // is the natural reference. The last step usually leads to the user's
    // chosen non-station destination, so we suppress the popup there to
    // avoid a confusing "station not found" dialog.
    //
    // Walking steps coming from Google Directions usually arrive without a
    // populated `to_station`, so we additionally try to parse the
    // instruction text ("Walk to KL Sentral") to recover a station name
    // for the popup trigger.
    const isLast = index === allSteps.length - 1;
    const prevStep = index > 0 ? allSteps[index - 1] : null;
    const nextStep = index < allSteps.length - 1 ? allSteps[index + 1] : null;
    const explicitStation = step.to_station || step.from_station || null;
    const inferredStation = extractStationNameFromInstruction(step.instruction);
    const stationForPopup = !isLast
      ? explicitStation || inferredStation
      : step.step_type === 'transit'
        ? explicitStation || inferredStation
        : null;
    const isTransferWalk =
      step.step_type === 'walking' &&
      prevStep?.step_type === 'transit' &&
      nextStep?.step_type === 'transit';
    const appendStationSuffix =
      step.step_type === 'walking' && !isLast && Boolean(stationForPopup);
    return {
      step: step.step_number,
      title: normalizeStepTitle(
        step.instruction,
        step.step_type,
        step.from_station,
        step.to_station,
        isLast,
        currentRoute?.destination_name,
        appendStationSuffix,
        step.transit_line,
        step.transit_vehicle_type,
        step.transit_headsign,
      ),
      isTransferWalk,
      lineDirectionFrom:
        step.step_type === 'transit' && step.transit_direction_from ? step.transit_direction_from : null,
      lineDirectionTo:
        step.step_type === 'transit' && step.transit_direction_to ? step.transit_direction_to : null,
      duration: step.duration_minutes ? `${step.duration_minutes} ${t('routeMins')}` : t('routeTimeUnknown'),
      distance: step.step_type === 'walking' && step.distance_meters ? `${step.distance_meters}m` : '',
      isWalking: step.step_type === 'walking',
      icon: step.step_type === 'walking' ? Footprints : step.step_type === 'transit' ? Train : MapPin,
      color: step.step_type === 'walking' ? BRAND_COLORS.blue : step.step_type === 'transit' ? BRAND_COLORS.green : BRAND_COLORS.warning,
      accessibility: localizeAccessibilityMessage(step.annotation.message),
      stationForPopup,
      seatAvailabilityLevel: (() => {
        const pct = getSeatProbabilityForRouteStep(
          {
            step_type: step.step_type,
            from_station: step.from_station,
            to_station: step.to_station,
            stationForPopup,
          },
          stepStationDetails,
          travelDateForSeatLookup,
        );
        return pct != null ? getSeatAvailabilityLevel(pct) : null;
      })(),
    };
  }) || [];

  useEffect(() => {
    setStepStationDetails({});
    loadedStationKeysRef.current.clear();
  }, [currentRoute?.recommended_route_id]);

  useEffect(() => {
    if (!currentRoute?.steps?.length) return;
    const step = currentRoute.steps[currentStep];
    if (!step) return;

    const isLast = currentStep === currentRoute.steps.length - 1;
    const explicitStation = step.to_station || step.from_station || null;
    const inferredStation = extractStationNameFromInstruction(step.instruction);
    const stationKey = !isLast
      ? explicitStation || inferredStation
      : step.step_type === 'transit'
        ? explicitStation || inferredStation
        : null;

    if (!stationKey || loadedStationKeysRef.current.has(stationKey)) return;
    loadedStationKeysRef.current.add(stationKey);

    const controller = new AbortController();
    void resolveStationDetailByName(stationKey, controller.signal).then((detail) => {
      if (!controller.signal.aborted) {
        setStepStationDetails((prev) => ({ ...prev, [stationKey]: detail }));
      }
    });

    return () => {
      controller.abort();
    };
  }, [currentRoute?.recommended_route_id, currentStep, currentRoute?.steps]);

  useEffect(() => {
    if (!currentRoute) {
      setRouteImageMap({});
      return;
    }
    if (!isCuratedCorridorRoute(currentRoute.origin_name, currentRoute.destination_name)) {
      setRouteImageMap({});
      return;
    }
    let cancelled = false;
    fetchRouteStationImageMap(CANONICAL_KLCC_MONASH_ROUTE_KEY)
      .then((map) => {
        if (!cancelled) setRouteImageMap(map);
      })
      .catch(() => {
        if (!cancelled) setRouteImageMap({});
      });
    return () => {
      cancelled = true;
    };
  }, [currentRoute?.recommended_route_id, currentRoute?.origin_name, currentRoute?.destination_name]);

  useEffect(() => {
    setStepImageIndex(0);
  }, [currentStep]);

  const resolveStepImages = (
    step: {
      isWalking: boolean;
      stationForPopup: string | null;
    },
    stepIndex: number,
  ): RouteStationImage[] => {
    const useCuratedCsv =
      currentRoute &&
      isCuratedCorridorRoute(currentRoute.origin_name, currentRoute.destination_name);

    if (useCuratedCsv) {
      const curated = currentRoute.steps[stepIndex]?.curated_images;
      if (curated && curated.length > 0) {
        return curated.map((image) => ({
          path: image.path,
          caption: image.caption || '',
        }));
      }

      const stepImages = getCustomRouteStepImages(routeImageMap, stepIndex);
      if (stepImages.length > 0) return stepImages;
    }

    const isLastStep = stepIndex === routeSteps.length - 1;
    const showPlaceImageOnly = Boolean(step.isWalking && isLastStep && !step.stationForPopup);
    const detail = step.stationForPopup ? stepStationDetails[step.stationForPopup] : undefined;

    if (showPlaceImageOnly) {
      const label = destination?.displayName || currentRoute?.destination_name;
      if (label) {
        return [
          {
            path: getStationStaticImageUrl(
              toLocationLabel(label),
              destination?.lat ?? null,
              destination?.lon ?? null,
            ),
            caption: '',
          },
        ];
      }
      return [];
    }

    if (step.stationForPopup) {
      if (useCuratedCsv) {
        const custom = getCustomStationImages(routeImageMap, step.stationForPopup);
        if (custom.length > 0) return custom;
      }
      if (detail?.name) {
        return [
          {
            path: getStationStaticImageUrl(detail.name, detail.lat ?? null, detail.lon ?? null),
            caption: '',
          },
        ];
      }
      const googlePath = getStationStaticImageUrl(cleanStationQuery(step.stationForPopup));
      return [{ path: googlePath, caption: '' }];
    }

    return [];
  };

  const scroll = (direction: 'left' | 'right') => {
    if (direction === 'left' && currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else if (direction === 'right' && currentStep < routeSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;

  useEffect(() => {
    if (!currentRoute) {
      setWeather(null);
      setWeatherStatus('idle');
      return;
    }

    // Prevent stale async weather responses from overwriting newer route selections.
    let cancelled = false;
    setWeatherStatus('loading');
    getDestinationWeather({
      destinationName: destination?.displayName || currentRoute.destination_name,
      lat: destination?.lat,
      lon: destination?.lon,
      departureTime
    })
      .then((nextWeather) => {
        if (cancelled) return;
        setWeather(nextWeather);
        setWeatherStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setWeather(null);
        setWeatherStatus('unavailable');
      });

    return () => {
      cancelled = true;
    };
  }, [currentRoute?.recommended_route_id, currentRoute?.destination_name, departureTime, destination?.displayName, destination?.lat, destination?.lon]);

  const plannedDestinationLabel = destination?.displayName
    ? toLocationLabel(destination.displayName)
    : currentRoute
      ? toLocationLabel(currentRoute.destination_name)
      : t('routeWeatherTitle');

  const geocodedAreaLabel = weather ? toLocationLabel(weather.destinationName) : '';
  const showGeocodedHint =
    Boolean(geocodedAreaLabel) &&
    geocodedAreaLabel.toLowerCase() !== plannedDestinationLabel.toLowerCase();

  const weatherLeavingLabel = () => {
    if (!departureTime) return '-';
    const customIso = departureTime.includes('T') ? departureTime : undefined;
    const preset = customIso ? 'now' : departureTime;
    const timeLabel = formatDepartureContextLabel(preset, language, customIso);
    return t('planTimeLeavingAt').replace('{time}', timeLabel);
  };

  const weatherDepartureDate = resolveDepartureDate(
    departureTime?.includes('T') ? 'now' : departureTime || 'now',
    departureTime?.includes('T') ? departureTime : undefined,
  );

  const formatNavigationPoint = (place: typeof origin, fallbackName: string) => {
    if (place && typeof place.lat === 'number' && typeof place.lon === 'number') {
      return `${place.lat},${place.lon}`;
    }
    return place?.displayName || fallbackName;
  };

  const buildGoogleMapsDirectionsUrl = () => {
    if (!currentRoute) return window.location.href;
    return buildMapsDirectionsUrl({
      origin: { label: formatNavigationPoint(origin, currentRoute.origin_name) },
      destination: { label: formatNavigationPoint(destination, currentRoute.destination_name) },
      waypoints: currentRoute.navigation_waypoints ?? [],
    });
  };

  const buildShareableRouteLink = () => {
    if (!currentRoute) return window.location.href;
    return buildGoogleMapsDirectionsUrl();
  };

  const showHint = (message: string) => {
    setActionHint(message);
    window.setTimeout(() => setActionHint(null), 2200);
  };

  const mapEmbedSrc = currentRoute
    ? GOOGLE_MAPS_EMBED_KEY
      ? `https://www.google.com/maps/embed/v1/directions?key=${encodeURIComponent(GOOGLE_MAPS_EMBED_KEY)}&origin=${encodeURIComponent(currentRoute.origin_name)}&destination=${encodeURIComponent(currentRoute.destination_name)}&mode=transit`
      // Fallback keeps map view functional even without Maps Embed API key.
      : `https://www.google.com/maps?output=embed&saddr=${encodeURIComponent(currentRoute.origin_name)}&daddr=${encodeURIComponent(currentRoute.destination_name)}&dirflg=r`
    : null;

  const handleSaveRouteImage = async () => {
    if (!currentRoute || routeSteps.length === 0) {
      showHint(t('routeSaveUnavailable'));
      return;
    }

    const drawRoundedRect = (
      ctx: CanvasRenderingContext2D,
      x: number,
      y: number,
      width: number,
      height: number,
      radius: number
    ) => {
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + width - radius, y);
      ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
      ctx.lineTo(x + width, y + height - radius);
      ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
      ctx.lineTo(x + radius, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
    };

    const wrapLines = (ctx: CanvasRenderingContext2D, text: string, maxWidth: number) => {
      const words = text.split(' ');
      const lines: string[] = [];
      let current = '';
      for (const word of words) {
        const test = current ? `${current} ${word}` : word;
        if (ctx.measureText(test).width <= maxWidth) {
          current = test;
        } else {
          if (current) lines.push(current);
          current = word;
        }
      }
      if (current) lines.push(current);
      return lines;
    };

    const drawLineDirection = (
      ctx: CanvasRenderingContext2D,
      x: number,
      y: number,
      maxWidth: number,
      from: string,
      to: string,
    ) => {
      const prefix = `${t('routeLineDirectionFrom')} `;
      const middle = ` ${t('routeLineDirectionTo')} `;
      ctx.fillStyle = BRAND_COLORS.navy;
      ctx.font = '500 38px Poppins, sans-serif';
      let cursorX = x;
      ctx.fillText(prefix, cursorX, y, maxWidth);
      cursorX += ctx.measureText(prefix).width;
      ctx.font = '700 38px Poppins, sans-serif';
      ctx.fillText(from, cursorX, y, maxWidth - (cursorX - x));
      cursorX += ctx.measureText(from).width;
      ctx.font = '500 38px Poppins, sans-serif';
      ctx.fillText(middle, cursorX, y, maxWidth - (cursorX - x));
      cursorX += ctx.measureText(middle).width;
      ctx.font = '700 38px Poppins, sans-serif';
      ctx.fillText(to, cursorX, y, maxWidth - (cursorX - x));
    };

    /**
     * Resolve a station/destination preview image into a canvas-drawable
     * HTMLImageElement. We swallow load failures so the rest of the card
     * still draws — image is purely supplemental.
     */
    const loadImage = (src: string): Promise<HTMLImageElement | null> =>
      new Promise((resolve) => {
        const img = new Image();
        try {
          const resolved = new URL(src, window.location.href);
          if (resolved.origin !== window.location.origin) {
            img.crossOrigin = 'anonymous';
          }
        } catch {
          img.crossOrigin = 'anonymous';
        }
        img.onload = () => resolve(img);
        img.onerror = () => resolve(null);
        img.src = src;
      });

    try {
      const width = 1080;
      const padding = 64;
      const cardGap = 30;
      const contentWidth = width - padding * 2;
      const stepTitleWidth = contentWidth - 200;
      const cardLeftPadding = 58;
      const cardInnerWidth = contentWidth - cardLeftPadding * 2;
      const imageHeight = 360;
      const chipHeight = 48;
      const chipGap = 12;

      // Build per-step download model that mirrors the render code so the
      // exported PNG matches what the user sees on screen (highlights, image,
      // walking-vs-transit detail line).
      const downloadSteps = currentRoute.steps.map((step, index, allSteps) => {
        const isLast = index === allSteps.length - 1;
        const explicitStation = step.to_station || step.from_station || null;
        const inferredStation = extractStationNameFromInstruction(step.instruction);
        const stationForPopup = !isLast
          ? explicitStation || inferredStation
          : step.step_type === 'transit'
            ? explicitStation || inferredStation
            : null;
        const detail = stationForPopup ? stepStationDetails[stationForPopup] ?? null : null;
        const highlights = detail?.station_facilities?.length
          ? getElderHighlightFacilities(detail.station_facilities)
          : [];

        const view = routeSteps[index];
        const stepImages = resolveStepImages(
          { isWalking: view.isWalking, stationForPopup },
          index,
        );

        return {
          step: view.step,
          title: view.title,
          duration: view.duration,
          distance: view.distance,
          isWalking: view.isWalking,
          color: view.color,
          lineDirectionFrom: view.lineDirectionFrom,
          lineDirectionTo: view.lineDirectionTo,
          highlights,
          images: stepImages.map((img) => ({
            path: img.path,
            caption: img.caption?.trim() ?? '',
          })),
        };
      });

      // Prefetch every step image (all carousel slides) in parallel.
      const loadedStepImages = await Promise.all(
        downloadSteps.map((step) =>
          Promise.all(
            step.images.map((img) =>
              img.path ? loadImage(resolveRouteImageUrl(img.path)) : Promise.resolve(null),
            ),
          ),
        ),
      );

      const preCanvas = document.createElement('canvas');
      const preCtx = preCanvas.getContext('2d');
      if (!preCtx) {
        showHint(t('routeSaveFailed'));
        return;
      }

      // Wrap facility chips into rows up-front so we can size each card.
      // Each chip carries both the canonical English value (used for icon
      // picking + tier classification) and the localized label that gets
      // drawn so users see the right language in the export.
      type LocalizedChip = { english: string; localized: string };
      type LaidOutChip = LocalizedChip & { x: number; y: number; width: number };
      const layoutFacilityChips = (chips: LocalizedChip[]): LaidOutChip[][] => {
        if (!chips.length) return [];
        preCtx.font = '700 30px Poppins, sans-serif';
        const rows: LaidOutChip[][] = [];
        let currentRow: LaidOutChip[] = [];
        let cursor = 0;
        let rowY = 0;
        chips.forEach((chip) => {
          const measured = preCtx.measureText(chip.localized).width;
          const w = measured + 36; // 18px horizontal padding each side
          if (cursor > 0 && cursor + w > cardInnerWidth) {
            rows.push(currentRow);
            currentRow = [];
            cursor = 0;
            rowY += chipHeight + chipGap;
          }
          currentRow.push({ ...chip, x: cursor, y: rowY, width: w });
          cursor += w + chipGap;
        });
        if (currentRow.length) rows.push(currentRow);
        return rows;
      };

      preCtx.font = 'bold 48px Poppins, sans-serif';
      const captionLineHeight = 42;
      const stepHeights = downloadSteps.map((step, idx) => {
        const titleLines = wrapLines(preCtx, step.title, stepTitleWidth);
        const localizedHighlights: LocalizedChip[] = step.highlights.map((label) => ({
          english: label,
          localized: translateFacility(label, language),
        }));
        const chipRows = layoutFacilityChips(localizedHighlights);
        const facilitiesBlockHeight = step.highlights.length
          ? 50 /* section label */ + chipRows.length * chipHeight + (chipRows.length - 1) * chipGap + 30 /* trailing margin */
          : 0;
        const detailLine = step.isWalking
          ? step.distance ? `${t('routeDistance')}: ${step.distance}` : ''
          : `${t('routeDuration')}: ${step.duration}`;
        const detailHeight = detailLine ? 60 : 0;
        const lineDirectionHeight =
          step.lineDirectionFrom && step.lineDirectionTo ? 50 : 0;
        const headerHeight = 110; // step number circle + label
        const titleSpacing = 54;
        const titleHeight = titleLines.length * titleSpacing + 30;
        const cardPaddingV = 80;

        preCtx.font = '500 34px Poppins, sans-serif';
        const imageBlocks = step.images.map((meta, imageIdx) => {
          const img = loadedStepImages[idx]?.[imageIdx] ?? null;
          if (!img) return { img: null, captionLines: [] as string[], height: 0 };
          const captionLines = meta.caption ? wrapLines(preCtx, meta.caption, cardInnerWidth) : [];
          const captionHeight = captionLines.length
            ? captionLines.length * captionLineHeight + 16
            : 0;
          return {
            img,
            captionLines,
            height: imageHeight + 24 + captionHeight + 20,
          };
        });
        const imagesBlockHeight = imageBlocks.reduce((sum, block) => sum + block.height, 0);

        return {
          titleLines,
          chipRows,
          detailLine,
          detailHeight,
          lineDirectionHeight,
          facilitiesBlockHeight,
          imageBlocks,
          height:
            cardPaddingV +
            headerHeight +
            titleHeight +
            lineDirectionHeight +
            detailHeight +
            facilitiesBlockHeight +
            imagesBlockHeight +
            24,
        };
      });

      const totalStepsHeight =
        stepHeights.reduce((sum, item) => sum + item.height, 0) +
        cardGap * Math.max(downloadSteps.length - 1, 0);

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = 320 + totalStepsHeight + 80;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        showHint(t('routeSaveFailed'));
        return;
      }

      ctx.fillStyle = BRAND_COLORS.bg;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const routeTitle = `${toLocationLabel(currentRoute.origin_name)} ${t('routeTo')} ${toLocationLabel(currentRoute.destination_name)}`;
      ctx.fillStyle = BRAND_COLORS.navy;
      ctx.font = '700 52px Poppins, sans-serif';
      ctx.fillText(routeTitle, padding, 90, contentWidth);

      drawRoundedRect(ctx, padding, 120, contentWidth, 120, 24);
      ctx.fillStyle = BRAND_COLORS.white;
      ctx.fill();
      ctx.strokeStyle = BRAND_COLORS.border;
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = BRAND_COLORS.blue;
      ctx.font = '700 42px Poppins, sans-serif';
      ctx.fillText(`${currentRoute.duration_minutes ?? '-'} ${t('routeMins')}`, padding + 40, 178);
      ctx.fillText(`${currentRoute.transfers ?? '-'}`, padding + 390, 178);
      ctx.fillText(`${currentRoute.walking_distance_meters ?? '-'}m`, padding + 620, 178);

      ctx.fillStyle = BRAND_COLORS.muted;
      ctx.font = '500 30px Poppins, sans-serif';
      ctx.fillText(t('routeTime'), padding + 40, 220);
      ctx.fillText(t('routeTransfers'), padding + 390, 220);
      ctx.fillText(t('routeWalk'), padding + 620, 220);

      ctx.fillStyle = BRAND_COLORS.navy;
      ctx.font = '700 50px Poppins, sans-serif';
      ctx.fillText(t('routeStepByStep'), padding, 300);

      let y = 330;
      downloadSteps.forEach((step, index) => {
        const { titleLines, chipRows, detailLine, detailHeight, lineDirectionHeight, facilitiesBlockHeight, imageBlocks, height } =
          stepHeights[index];

        // Card background + left color stripe
        drawRoundedRect(ctx, padding, y, contentWidth, height, 28);
        ctx.fillStyle = BRAND_COLORS.white;
        ctx.fill();
        ctx.fillStyle = step.color;
        ctx.fillRect(padding, y, 10, height);

        // Step number circle + "Step X of Y" label
        ctx.beginPath();
        ctx.arc(padding + cardLeftPadding, y + 58, 34, 0, Math.PI * 2);
        ctx.fillStyle = step.color;
        ctx.fill();
        ctx.fillStyle = BRAND_COLORS.white;
        ctx.font = '700 34px Poppins, sans-serif';
        ctx.fillText(String(step.step), padding + cardLeftPadding - 11, y + 71);

        ctx.fillStyle = BRAND_COLORS.muted;
        ctx.font = '600 34px Poppins, sans-serif';
        ctx.fillText(
          `${t('routeStep')} ${step.step} ${t('routeOf')} ${downloadSteps.length}`,
          padding + cardLeftPadding + 67,
          y + 72,
        );

        // Title (wrapped)
        ctx.fillStyle = BRAND_COLORS.navy;
        ctx.font = '700 52px Poppins, sans-serif';
        let textY = y + 138;
        titleLines.forEach((line) => {
          ctx.fillText(line, padding + cardLeftPadding, textY, cardInnerWidth);
          textY += 54;
        });
        textY += 16; // small spacing under title

        if (step.lineDirectionFrom && step.lineDirectionTo && lineDirectionHeight) {
          drawLineDirection(
            ctx,
            padding + cardLeftPadding,
            textY + 8,
            cardInnerWidth,
            step.lineDirectionFrom,
            step.lineDirectionTo,
          );
          textY += lineDirectionHeight;
        }

        // Detail line: walking shows distance only, others show duration
        if (detailLine) {
          ctx.fillStyle = BRAND_COLORS.body;
          ctx.font = '500 38px Poppins, sans-serif';
          ctx.fillText(detailLine, padding + cardLeftPadding, textY + 8, cardInnerWidth);
          textY += detailHeight;
        }

        // Highlighted facilities (Tier 1 = solid blue, Tier 2 = light blue)
        if (step.highlights.length) {
          ctx.fillStyle = BRAND_COLORS.muted;
          ctx.font = '700 24px Poppins, sans-serif';
          ctx.fillText(t('stationFacilities').toUpperCase(), padding + cardLeftPadding, textY + 18);
          const chipsBaseX = padding + cardLeftPadding;
          const chipsBaseY = textY + 36;
          ctx.font = '700 30px Poppins, sans-serif';
          chipRows.forEach((row) => {
            row.forEach((chip) => {
              const tier = getFacilityTier(chip.english);
              const cx = chipsBaseX + chip.x;
              const cy = chipsBaseY + chip.y;
              drawRoundedRect(ctx, cx, cy, chip.width, chipHeight, 24);
              if (tier === 1) {
                ctx.fillStyle = BRAND_COLORS.blue;
                ctx.fill();
                ctx.fillStyle = BRAND_COLORS.white;
              } else {
                ctx.fillStyle = 'rgba(74, 144, 226, 0.18)';
                ctx.fill();
                ctx.fillStyle = BRAND_COLORS.navy;
              }
              ctx.fillText(chip.localized, cx + 18, cy + 33);
            });
          });
          textY += facilitiesBlockHeight;
        }

        // All step photos + captions (same content as the on-screen carousel).
        imageBlocks.forEach((block) => {
          if (!block.img) return;
          const imgX = padding + cardLeftPadding;
          const imgW = cardInnerWidth;
          const imgH = imageHeight;
          const aspectImg = block.img.width / block.img.height;
          const aspectRect = imgW / imgH;
          let sx = 0;
          let sy = 0;
          let sw = block.img.width;
          let sh = block.img.height;
          if (aspectImg > aspectRect) {
            sw = block.img.height * aspectRect;
            sx = (block.img.width - sw) / 2;
          } else {
            sh = block.img.width / aspectRect;
            sy = (block.img.height - sh) / 2;
          }
          ctx.save();
          drawRoundedRect(ctx, imgX, textY, imgW, imgH, 18);
          ctx.clip();
          ctx.drawImage(block.img, sx, sy, sw, sh, imgX, textY, imgW, imgH);
          ctx.restore();
          ctx.strokeStyle = BRAND_COLORS.border;
          ctx.lineWidth = 2;
          drawRoundedRect(ctx, imgX, textY, imgW, imgH, 18);
          ctx.stroke();
          textY += imgH + 24;

          if (block.captionLines.length) {
            ctx.fillStyle = BRAND_COLORS.body;
            ctx.font = '500 34px Poppins, sans-serif';
            block.captionLines.forEach((line) => {
              ctx.fillText(line, imgX, textY + 8, cardInnerWidth);
              textY += captionLineHeight;
            });
            textY += 16;
          }
          textY += 4;
        });

        y += height + cardGap;
      });

      // Use client-side download so users can save/share route summaries instantly.
      const link = document.createElement('a');
      link.href = canvas.toDataURL('image/png');
      link.download = `eldergo-route-${new Date().toISOString().slice(0, 10)}.png`;
      link.click();
      showHint(t('routeSaveSuccess'));
    } catch {
      showHint(t('routeSaveFailed'));
    }
  };

  const handleCopyShareLink = async () => {
    const link = buildShareableRouteLink();
    try {
      await navigator.clipboard.writeText(link);
      showHint(t('routeCopySuccess'));
      setShareMenuOpen(false);
    } catch {
      showHint(t('routeCopyFailed'));
    }
  };

  const handleWhatsAppShare = () => {
    const shareText = `${t('routeShareMessage')} ${buildShareableRouteLink()}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(shareText)}`, '_blank', 'noopener,noreferrer');
    setShareMenuOpen(false);
  };

  const handleStartNavigation = () => {
    if (!currentRoute) return;
    const webUrl = buildGoogleMapsDirectionsUrl();
    const destinationLabel = formatNavigationPoint(destination, currentRoute.destination_name);

    attemptOpenGoogleMaps({
      webUrl,
      destinationLabel,
      onMapsMissing: () => setShowMapsInstallModal(true),
    });
  };

  const handleInstallGoogleMaps = () => {
    openGoogleMapsStore(navigator.userAgent);
    setShowMapsInstallModal(false);
  };

  const handleOpenMapsInBrowser = () => {
    const webUrl = buildGoogleMapsDirectionsUrl();
    window.open(webUrl, '_blank', 'noopener,noreferrer');
    setShowMapsInstallModal(false);
  };

  const showRouteUnavailable = Boolean(routeError && !currentRoute && !routeLoading);

  if (showRouteUnavailable) {
    return (
      <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
        <div
          className="fixed inset-0 z-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(/background-elder.png)' }}
        />
        <div
          className="fixed inset-0 z-0"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12',
          }}
        />
        <div className="relative z-10">
          <TopBar onLogoClick={onNavigateToPlanTime} />
          <main className="pt-20 pb-44 px-6">
            <div className="max-w-2xl mx-auto mt-6">
              <RouteUnavailableView
                variant={routeErrorCode === 'no_transit_route' ? 'no_transit' : 'generic'}
                departureTime={departureTime}
                origin={origin}
                destination={destination}
                baseFontSize={baseFontSize}
                language={language}
                message={routeError}
                t={t}
                onNavigateToPlanTime={onNavigateToPlanTime}
                onNavigateToPlanning={onNavigateToPlanning}
              />
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
        </div>
      </div>
    );
  }

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
      <TopBar onLogoClick={onNavigateToPlanTime} />

      <main className="pt-20 pb-44 px-6">
        <div
          className="max-w-2xl mx-auto mt-6 relative min-h-[50vh]"
          aria-busy={routeLoading}
        >
          {routeLoading ? (
            <>
              <RouteResultSkeleton baseFontSize={baseFontSize} />
              <div className="absolute inset-0 z-30 flex items-center justify-center px-4">
                <div
                  className="absolute inset-0 bg-white/55 backdrop-blur-sm"
                  aria-hidden
                />
                <RouteLoadingPanel
                  origin={origin}
                  destination={destination}
                  baseFontSize={baseFontSize}
                  t={t}
                />
              </div>
            </>
          ) : (
            <>
          {!currentRoute && (
            <div className="bg-white/95 p-6 rounded-2xl shadow-md mb-6">
              <h3 className="text-[24px] font-semibold text-eldergo-navy mb-3">
                {t('routeNoSelectionTitle')}
              </h3>
              <p className="text-[18px] text-eldergo-muted mb-5">
                {routeError || t('routeNoSelectionBody')}
              </p>
              <button
                onClick={onNavigateToPlanning}
                className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark text-white font-semibold py-4 rounded-xl transition-colors shadow-md"
              >
                {t('routePlanRoute')}
              </button>
            </div>
          )}

          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setViewMode('text')}
              className={`flex-1 py-3 rounded-full font-semibold text-[18px] transition-all ${
                viewMode === 'text'
                  ? 'bg-eldergo-blue text-white'
                  : 'bg-white text-eldergo-navy border-2 border-eldergo-border'
              }`}
            >
              {t('routeTextView')}
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex-1 py-3 rounded-full font-semibold text-[18px] transition-all ${
                viewMode === 'map'
                  ? 'bg-eldergo-blue text-white'
                  : 'bg-white text-eldergo-navy border-2 border-eldergo-border'
              }`}
            >
              {t('routeMapView')}
            </button>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-md mb-6">
            <div className="mb-5">
              {currentRoute ? (
                <div className="text-center">
                  <h3
                    className="font-semibold text-eldergo-navy leading-tight"
                    style={{ fontSize: `${28 * baseFontSize}px` }}
                  >
                    {toLocationLabel(currentRoute.origin_name)}
                  </h3>
                  <div className="flex justify-center py-2">
                    <ArrowDown size={28 * baseFontSize} strokeWidth={2.8} className="text-eldergo-blue" />
                  </div>
                  <h3
                    className="font-semibold text-eldergo-navy leading-tight"
                    style={{ fontSize: `${28 * baseFontSize}px` }}
                  >
                    {toLocationLabel(currentRoute.destination_name)}
                  </h3>
                </div>
              ) : (
                <h3 className="text-[24px] font-semibold text-eldergo-navy text-center">
                  {t('routeNotSelected')}
                </h3>
              )}
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="font-bold text-eldergo-blue tabular-nums" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {currentRoute?.duration_minutes ?? '-'} {t('routeMins')}
                </div>
                <div className="text-eldergo-muted" style={{ fontSize: `${14 * baseFontSize}px` }}>
                  {t('routeTime')}
                </div>
              </div>
              <div>
                <div className="font-bold text-eldergo-blue tabular-nums" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {currentRoute?.transfers ?? '-'}
                </div>
                <div className="text-eldergo-muted" style={{ fontSize: `${14 * baseFontSize}px` }}>
                  {t('routeTransfers')}
                </div>
              </div>
              <div>
                <div className="font-bold text-eldergo-blue tabular-nums" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {currentRoute?.walking_distance_meters ?? '-'}m
                </div>
                <div className="text-eldergo-muted" style={{ fontSize: `${14 * baseFontSize}px` }}>
                  {t('routeWalk')}
                </div>
              </div>
            </div>
            {currentRoute ? (
              <RouteRankingInsight
                primaryFactor={currentRoute.ranking_primary_factor}
                secondaryFactor={currentRoute.ranking_secondary_factor}
                baseFontSize={baseFontSize}
                t={t}
              />
            ) : null}
          </div>

          <button
            type="button"
            onClick={handleStartNavigation}
            disabled={!currentRoute}
            className="w-full mb-6 inline-flex items-center justify-center gap-3 bg-eldergo-blue hover:bg-eldergo-blue-dark text-white font-bold rounded-2xl shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              fontSize: `${20 * baseFontSize}px`,
              paddingTop: `${16 * baseFontSize}px`,
              paddingBottom: `${16 * baseFontSize}px`,
            }}
            aria-label={t('routeStartNavigationAria')}
          >
            <Navigation
              size={22 * baseFontSize}
              strokeWidth={2.6}
              className="text-white"
              fill="currentColor"
              fillOpacity={0.25}
            />
            {t('routeStartNavigation')}
          </button>

          {viewMode === 'text' ? (
            <div className="relative mb-8">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-[20px] font-semibold text-eldergo-navy" style={{ fontSize: `${20 * baseFontSize}px` }}>
                  {t('routeStepByStep')}
                </h4>
                <div className="relative flex gap-2">
                  <button
                    onClick={handleSaveRouteImage}
                    className="w-12 h-12 bg-eldergo-blue hover:bg-eldergo-blue-dark rounded-full flex items-center justify-center transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!currentRoute}
                    aria-label={t('routeSaveAction')}
                  >
                    <Download size={22} strokeWidth={2.5} className="text-white" />
                  </button>
                  <button
                    onClick={() => setShareMenuOpen((prev) => !prev)}
                    className="w-12 h-12 bg-eldergo-green hover:bg-eldergo-green-dark rounded-full flex items-center justify-center transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!currentRoute}
                    aria-label={t('routeShareAction')}
                  >
                    <Share2 size={22} strokeWidth={2.5} className="text-white" />
                  </button>
                  {shareMenuOpen && (
                    <div className="absolute right-0 top-14 bg-white border border-eldergo-border rounded-xl shadow-xl p-2 min-w-[210px] z-20">
                      <button
                        onClick={handleWhatsAppShare}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-eldergo-bg text-eldergo-navy font-medium"
                      >
                        {t('routeShareWhatsApp')}
                      </button>
                      <button
                        onClick={handleCopyShareLink}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-eldergo-bg text-eldergo-navy font-medium"
                      >
                        {t('routeShareCopyLink')}
                      </button>
                    </div>
                  )}
                </div>
              </div>
              {actionHint && (
                <div className="mb-3 rounded-lg bg-eldergo-green/15 text-eldergo-green px-4 py-3 text-[15px] font-medium">
                  {actionHint}
                </div>
              )}

              <div className="relative">
                {currentStep > 0 && (
                  <button
                    type="button"
                    onClick={() => scroll('left')}
                    className="absolute -left-2 sm:left-2 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border-2 border-eldergo-border bg-white/95 shadow-lg backdrop-blur-sm transition-all hover:border-eldergo-blue hover:bg-white sm:h-12 sm:w-12"
                    aria-label={t('routeStepPrevious')}
                  >
                    <ChevronLeft size={20} strokeWidth={2.5} className="text-eldergo-navy sm:h-6 sm:w-6" />
                  </button>
                )}

                {currentStep < routeSteps.length - 1 && (
                  <button
                    type="button"
                    onClick={() => scroll('right')}
                    className="absolute -right-2 sm:right-2 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border-2 border-eldergo-border bg-white/95 shadow-lg backdrop-blur-sm transition-all hover:border-eldergo-blue hover:bg-white sm:h-12 sm:w-12"
                    aria-label={t('routeStepNext')}
                  >
                    <ChevronRight size={20} strokeWidth={2.5} className="text-eldergo-navy sm:h-6 sm:w-6" />
                  </button>
                )}

                <div className="overflow-hidden">
                  <div
                    className="flex transition-transform duration-300 ease-in-out"
                    style={{ transform: `translateX(-${currentStep * 100}%)` }}
                  >
                    {routeSteps.map((step, stepIndex) => {
                      const IconComponent = step.icon;
                      const isLastStep = stepIndex === routeSteps.length - 1;
                      const detail = step.stationForPopup ? stepStationDetails[step.stationForPopup] : undefined;
                      const resolvedStation =
                        Boolean(step.stationForPopup) &&
                        Object.prototype.hasOwnProperty.call(stepStationDetails, step.stationForPopup);
                      const highlights =
                        resolvedStation && detail?.station_facilities?.length
                          ? getElderHighlightFacilities(detail.station_facilities)
                          : [];
                      const showFacilityRow = highlights.length > 0;

                      const stepImages = resolveStepImages(step, stepIndex);
                      const safeImageIndex =
                        stepImages.length > 0 ? Math.min(stepImageIndex, stepImages.length - 1) : 0;
                      const activeImage = stepImages[safeImageIndex] ?? null;
                      const imageSrc = activeImage?.path ?? null;
                      const imageCaption = activeImage?.caption?.trim() ?? '';
                      const showImageBlock = stepImages.length > 0;

                      return (
                        <div
                          key={`route-step-${stepIndex}-${step.step}`}
                          className="w-full flex-shrink-0 px-6 sm:px-16"
                        >
                          <div
                            className="bg-white/95 backdrop-blur-sm p-5 sm:p-6 rounded-2xl shadow-xl border-l-4 flex flex-col overflow-y-auto"
                            style={{
                              borderLeftColor: step.color,
                              // Lock all step cards to the same scrollable
                              // height so the carousel stays steady when
                              // facilities/images differ between steps. The
                              // height scales with the user's font setting.
                              height: `${620 * baseFontSize}px`,
                              maxHeight: '82vh',
                            }}
                          >
                            <div className="flex flex-col flex-1 min-h-0">
                              <div className="flex items-center gap-3 mb-4">
                                <div
                                  className="w-10 h-10 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0"
                                  style={{
                                    backgroundColor: step.color,
                                    fontSize: `${16 * baseFontSize}px`,
                                  }}
                                >
                                  {step.step}
                                </div>
                                <div className="font-medium text-gray-500" style={{ fontSize: `${12 * baseFontSize}px` }}>
                                  {t('routeStep')} {step.step} {t('routeOf')} {routeSteps.length}
                                </div>
                              </div>

                              <div className="flex items-start gap-2 sm:gap-3 mb-3">
                                <IconComponent size={22 * baseFontSize} style={{ color: step.color }} strokeWidth={2.5} className="mt-1 flex-shrink-0" />
                                <div className="font-semibold text-eldergo-navy break-words leading-snug" style={{ fontSize: `${18 * baseFontSize}px` }}>
                                  {step.title}
                                </div>
                              </div>

                              {step.lineDirectionFrom && step.lineDirectionTo && (
                                <div
                                  className="text-eldergo-blue-dark font-medium mb-3 -mt-1"
                                  style={{ fontSize: `${15 * baseFontSize}px` }}
                                >
                                  {t('routeLineDirectionFrom')}{' '}
                                  <span className="font-bold">{step.lineDirectionFrom}</span>
                                  {' '}{t('routeLineDirectionTo')}{' '}
                                  <span className="font-bold">{step.lineDirectionTo}</span>
                                </div>
                              )}

                              {step.isTransferWalk && (
                                <div
                                  className="inline-flex items-center gap-2 self-start rounded-full bg-eldergo-warning/15 text-eldergo-warning border border-eldergo-warning/40 px-3 py-1.5 mb-3 font-semibold"
                                  style={{ fontSize: `${13 * baseFontSize}px` }}
                                  role="status"
                                >
                                  <ArrowRightLeft size={16 * baseFontSize} strokeWidth={2.5} aria-hidden />
                                  <span>{t('routeTransferWalk')}</span>
                                  <span className="font-medium opacity-90">· {t('routeTransferWalkHint')}</span>
                                </div>
                              )}

                              <div className="text-eldergo-muted mb-4" style={{ fontSize: `${16 * baseFontSize}px` }}>
                                {step.isWalking
                                  ? step.distance
                                    ? `${t('routeDistance')}: ${step.distance}`
                                    : ''
                                  : `${t('routeDuration')}: ${step.duration}`}
                              </div>

                              {step.seatAvailabilityLevel && (() => {
                                const level = step.seatAvailabilityLevel as SeatAvailabilityLevel;
                                const seatLevelConfig: Record<
                                  SeatAvailabilityLevel,
                                  { Icon: typeof Armchair; colorClass: string; textKey: 'routeSeatAvailabilityRelaxed' | 'routeSeatAvailabilityModerate' | 'routeSeatAvailabilityCrowded' }
                                > = {
                                  relaxed: {
                                    Icon: Armchair,
                                    colorClass: 'text-eldergo-green',
                                    textKey: 'routeSeatAvailabilityRelaxed',
                                  },
                                  moderate: {
                                    Icon: Users,
                                    colorClass: 'text-eldergo-warning',
                                    textKey: 'routeSeatAvailabilityModerate',
                                  },
                                  crowded: {
                                    Icon: AlertCircle,
                                    colorClass: 'text-red-600',
                                    textKey: 'routeSeatAvailabilityCrowded',
                                  },
                                };
                                const { Icon, colorClass, textKey } = seatLevelConfig[level];
                                const tierLabel = t(textKey);
                                return (
                                  <div
                                    className={`inline-flex items-center gap-2 self-start mb-4 font-medium ${colorClass}`}
                                    style={{ fontSize: `${15 * baseFontSize}px` }}
                                    role="status"
                                    aria-label={`${t('routeSeatAvailabilityLabel')} ${tierLabel}`}
                                  >
                                    <Icon size={16 * baseFontSize} strokeWidth={2.5} aria-hidden />
                                    <span>{t('routeSeatAvailabilityLabel')}</span>
                                    <span className="font-semibold">{tierLabel}</span>
                                  </div>
                                );
                              })()}

                              <div className="flex flex-col gap-4 pt-1 flex-1 min-h-0">
                                {step.stationForPopup && (
                                  <button
                                    type="button"
                                    onClick={() => setStationModalName(step.stationForPopup)}
                                    aria-label={t('routeViewStationDetails')}
                                    className="group inline-flex items-center justify-between gap-3 self-stretch bg-eldergo-blue/10 hover:bg-eldergo-blue/15 active:bg-eldergo-blue/20 text-eldergo-blue-dark font-semibold rounded-2xl border border-eldergo-blue/30 transition-colors"
                                    style={{
                                      fontSize: `${15 * baseFontSize}px`,
                                      paddingTop: `${12 * baseFontSize}px`,
                                      paddingBottom: `${12 * baseFontSize}px`,
                                      paddingLeft: `${18 * baseFontSize}px`,
                                      paddingRight: `${18 * baseFontSize}px`,
                                    }}
                                  >
                                    <span className="inline-flex items-center gap-2.5">
                                      <MapPin
                                        size={18 * baseFontSize}
                                        strokeWidth={2.4}
                                        className="text-eldergo-blue"
                                      />
                                      {t('routeViewStationDetails')}
                                    </span>
                                    <ChevronRight
                                      size={20 * baseFontSize}
                                      strokeWidth={2.4}
                                      className="text-eldergo-blue opacity-70 transition-transform group-hover:translate-x-0.5 group-hover:opacity-100"
                                    />
                                  </button>
                                )}

                                {showFacilityRow && (
                                  <div className="border-t border-eldergo-border pt-3">
                                    <div
                                      className="text-eldergo-muted font-semibold uppercase tracking-wide mb-2"
                                      style={{
                                        fontSize: `${11 * baseFontSize}px`,
                                        letterSpacing: '0.06em',
                                      }}
                                    >
                                      {t('stationFacilities')}
                                    </div>
                                    <div className="flex flex-wrap gap-x-4 gap-y-2 select-none">
                                      {highlights.map((item) => {
                                        const FIcon = pickFacilityIcon(item);
                                        const tier = getFacilityTier(item);
                                        // Render as inline icon + label badges
                                        // (no border, no fill button shape) so
                                        // users don't mistake them for tappable
                                        // controls. Tier 1 still gets visual
                                        // prominence via color + weight.
                                        const textClass =
                                          tier === 1
                                            ? 'text-eldergo-blue-dark font-bold'
                                            : 'text-eldergo-navy font-semibold';
                                        const iconClass =
                                          tier === 1 ? 'text-eldergo-blue' : 'text-eldergo-blue/70';
                                        return (
                                          <span
                                            key={item}
                                            className={`inline-flex items-center gap-1.5 cursor-default ${textClass}`}
                                            style={{ fontSize: `${14 * baseFontSize}px` }}
                                          >
                                            <FIcon
                                              size={16 * baseFontSize}
                                              className={`${iconClass} flex-shrink-0`}
                                              strokeWidth={tier === 1 ? 2.4 : 2.2}
                                            />
                                            <span>{translateFacility(item, language)}</span>
                                          </span>
                                        );
                                      })}
                                    </div>
                                  </div>
                                )}

                                {showImageBlock && imageSrc && (
                                  // flex-1 lets the image grow to fill the
                                  // empty space below the button/chips so the
                                  // card looks balanced. min-h-[160px] keeps
                                  // it from collapsing when the card has lots
                                  // of facility chips.
                                  <div className="flex-1 min-h-[160px] flex flex-col gap-2">
                                    <div className="relative flex-1 min-h-[160px] rounded-xl overflow-hidden border border-eldergo-border shadow-sm">
                                      <ImageWithFallback
                                        src={imageSrc}
                                        alt={
                                          imageCaption ||
                                          detail?.name ||
                                          step.stationForPopup ||
                                          toLocationLabel(destination?.displayName) ||
                                          'Destination'
                                        }
                                        className="w-full h-full object-cover"
                                      />
                                      {stepImages.length > 1 && safeImageIndex > 0 && (
                                        <button
                                          type="button"
                                          onClick={() => setStepImageIndex((prev) => Math.max(0, prev - 1))}
                                          className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full border border-eldergo-border bg-white/90 p-2 shadow-md"
                                          aria-label={t('routePhotoPrevious')}
                                        >
                                          <ChevronLeft size={20} className="text-eldergo-navy" />
                                        </button>
                                      )}
                                      {stepImages.length > 1 &&
                                        safeImageIndex < stepImages.length - 1 && (
                                          <button
                                            type="button"
                                            onClick={() =>
                                              setStepImageIndex((prev) =>
                                                Math.min(stepImages.length - 1, prev + 1),
                                              )
                                            }
                                            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full border border-eldergo-border bg-white/90 p-2 shadow-md"
                                            aria-label={t('routePhotoNext')}
                                          >
                                            <ChevronRight size={20} className="text-eldergo-navy" />
                                          </button>
                                        )}
                                    </div>
                                    {imageCaption && (
                                      <p
                                        className="text-center text-eldergo-navy/85 px-3 leading-snug"
                                        style={{ fontSize: `${14 * baseFontSize}px` }}
                                      >
                                        {imageCaption}
                                      </p>
                                    )}
                                    {stepImages.length > 1 && (
                                      <div className="flex items-center justify-center gap-2">
                                        {stepImages.map((_, dotIndex) => (
                                          <button
                                            key={`route-step-image-dot-${stepIndex}-${dotIndex}`}
                                            type="button"
                                            onClick={() => setStepImageIndex(dotIndex)}
                                            className={`h-2.5 w-2.5 rounded-full ${
                                              dotIndex === safeImageIndex
                                                ? 'bg-eldergo-blue'
                                                : 'bg-eldergo-border'
                                            }`}
                                            aria-label={`Photo ${dotIndex + 1} of ${stepImages.length}`}
                                          />
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white p-4 rounded-2xl shadow-md mb-8">
              {mapEmbedSrc ? (
                <iframe
                  src={mapEmbedSrc}
                  width="100%"
                  height="400"
                  style={{ border: 0, borderRadius: '12px' }}
                  allowFullScreen
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              ) : (
                <div className="h-[400px] rounded-xl bg-eldergo-bg flex items-center justify-center text-eldergo-navy font-medium">
                  {t('routeMapEmpty')}
                </div>
              )}
            </div>
          )}

          {currentRoute ? (
            <RouteWeatherCard
              weather={weather}
              weatherStatus={weatherStatus}
              plannedDestinationLabel={plannedDestinationLabel}
              geocodedAreaLabel={geocodedAreaLabel}
              showGeocodedHint={showGeocodedHint}
              leavingLabel={weatherLeavingLabel()}
              departureTime={weatherDepartureDate}
              language={language}
              baseFontSize={baseFontSize}
              t={t}
            />
          ) : null}

            </>
          )}
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
      </div>

      <StationDetailModal
        isOpen={stationModalName !== null}
        onClose={() => setStationModalName(null)}
        stationName={stationModalName}
        baseFontSize={baseFontSize}
        t={t}
      />

      <GoogleMapsInstallModal
        isOpen={showMapsInstallModal}
        title={t('routeGoogleMapsInstallTitle')}
        body={t('routeGoogleMapsInstallBody')}
        installLabel={t('routeGoogleMapsInstallConfirm')}
        cancelLabel={t('routeGoogleMapsInstallCancel')}
        browserLabel={t('routeGoogleMapsOpenInBrowser')}
        baseFontSize={baseFontSize}
        onInstall={handleInstallGoogleMaps}
        onOpenInBrowser={handleOpenMapsInBrowser}
        onClose={() => setShowMapsInstallModal(false)}
      />
    </div>
  );
}
