import { useEffect, useState, useRef } from 'react';
import { Download, Share2, Cloud, CloudLightning, CloudRain, CloudSun, Sun, Train, MapPin, Footprints, ChevronLeft, ChevronRight, ArrowDown } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { getTranslation } from '../i18n/translations';
import { DestinationWeather, getDestinationWeather } from '../services/weatherApi';

interface RouteResultPageProps {
  onNavigateToPlanning: () => void;
  onNavigateToPlanTime: () => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
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
  onShowChatbot
}: RouteResultPageProps) {
  const [viewMode, setViewMode] = useState<'text' | 'map'>('text');
  const [currentStep, setCurrentStep] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { currentRoute, departureTime, destination, fontSize, routeError, language } = useAppContext();
  const [shareMenuOpen, setShareMenuOpen] = useState(false);
  const [actionHint, setActionHint] = useState<string | null>(null);
  const [weather, setWeather] = useState<DestinationWeather | null>(null);
  const [weatherStatus, setWeatherStatus] = useState<'idle' | 'loading' | 'ready' | 'unavailable'>('idle');
  const t = (key: string) => getTranslation(language, key as any);

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
    destinationName?: string | null
  ) => {
    const shortFrom = removeBracketContent(toLocationLabel(fromStation));
    const shortTo = removeBracketContent(toLocationLabel(toStation));
    const shortDestination = removeBracketContent(toLocationLabel(destinationName));
    const cleanedInstruction = removeBracketContent(instruction);
    const actionWalkTo = t('routeActionWalkTo');
    const actionArriveAt = t('routeActionArriveAt');
    const actionFrom = t('routeActionFrom');
    const actionTo = t('routeActionTo');

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
      const head = cleanedInstruction.split(/ from /i)[0];
      return `${head} ${actionFrom} ${shortFrom} ${actionTo} ${shortTo}`;
    }

    const walkToMatch = cleanedInstruction.match(/^(Walk to )(.+)$/i);
    if (walkToMatch) {
      return `${actionWalkTo} ${removeBracketContent(toLocationLabel(walkToMatch[2]))}`;
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

  const routeSteps = currentRoute?.steps.map((step, index, allSteps) => ({
    step: step.step_number,
    title: normalizeStepTitle(
      step.instruction,
      step.step_type,
      step.from_station,
      step.to_station,
      index === allSteps.length - 1,
      currentRoute?.destination_name
    ),
    duration: step.duration_minutes ? `${step.duration_minutes} ${t('routeMins')}` : t('routeTimeUnknown'),
    distance: step.step_type === 'walking' && step.distance_meters ? `${step.distance_meters}m` : '',
    icon: step.step_type === 'walking' ? Footprints : step.step_type === 'transit' ? Train : MapPin,
    color: step.step_type === 'walking' ? BRAND_COLORS.blue : step.step_type === 'transit' ? BRAND_COLORS.green : BRAND_COLORS.warning,
    accessibility: localizeAccessibilityMessage(step.annotation.message)
  })) || [];

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

    let cancelled = false;
    setWeatherStatus('loading');
    getDestinationWeather({
      destinationName: destination?.displayName || currentRoute.destination_name,
      lat: destination?.lat,
      lon: destination?.lon,
      departureTime: departureTime as 'now' | 'morning' | 'afternoon' | 'evening'
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

  const seniorWeatherTips = () => {
    if (weatherStatus === 'loading') return [t('routeWeatherSeniorLoading')];
    if (weatherStatus !== 'ready' || !weather) return [t('routeWeatherSeniorUnavailable')];
    const tipKeys = {
      storm: ['routeWeatherSeniorStorm1', 'routeWeatherSeniorStorm2'],
      rain: ['routeWeatherSeniorRain1', 'routeWeatherSeniorRain2'],
      hot: ['routeWeatherSeniorHot1', 'routeWeatherSeniorHot2'],
      clear: ['routeWeatherSeniorClear1', 'routeWeatherSeniorClear2'],
      unavailable: ['routeWeatherSeniorUnavailable']
    } as const;
    return tipKeys[weather.riskLevel].map((key) => t(key));
  };

  const weatherDestinationLabel = weather
    ? toLocationLabel(weather.destinationName)
    : currentRoute
      ? toLocationLabel(currentRoute.destination_name)
      : t('routeWeatherTitle');

  const weatherPeriodLabel = () => {
    if (weatherStatus !== 'ready' || !weather) return '-';
    const hasRainSignal = weather.riskLevel === 'rain' || weather.riskLevel === 'storm' || (weather.precipitationProbabilityPercent ?? 0) > 0 || weather.rainMm > 0;
    if (!hasRainSignal) return '-';
    const periodKeys = {
      now: 'planTimeNow',
      morning: 'planTimeMorning',
      afternoon: 'planTimeAfternoon',
      evening: 'planTimeEvening'
    } as const;
    return t(periodKeys[weather.periodLabel]);
  };

  const getWeatherIcon = () => {
    if (!weather) return Cloud;
    const description = `${weather.weatherMain} ${weather.weatherDescription}`.toLowerCase();
    if (weather.riskLevel === 'storm' || description.includes('thunder') || description.includes('storm')) return CloudLightning;
    if (weather.riskLevel === 'rain' || description.includes('rain') || description.includes('drizzle')) return CloudRain;
    if (weather.riskLevel === 'hot' || description.includes('clear')) return Sun;
    if (description.includes('cloud')) return Cloud;
    return CloudSun;
  };

  const WeatherIcon = getWeatherIcon();

  const weatherCard = (
    <div className="bg-white/95 border-2 border-eldergo-border p-5 rounded-2xl shadow-md mb-6">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 bg-eldergo-blue/15 rounded-full flex items-center justify-center flex-shrink-0">
          <WeatherIcon size={28} strokeWidth={2.5} className="text-eldergo-blue" />
        </div>
        <h3 className="text-[20px] font-semibold text-eldergo-navy leading-tight">
          {weatherDestinationLabel}
        </h3>
      </div>
      <div>
          {weatherStatus === 'ready' && weather && (
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="rounded-xl bg-eldergo-bg px-3 py-3">
                <div className="text-[20px] font-bold text-eldergo-blue">{weather.temperatureC}&deg;C</div>
                <div className="text-[13px] text-eldergo-muted">{t('routeWeatherTemp')}</div>
              </div>
              <div className="rounded-xl bg-eldergo-bg px-3 py-3">
                <div className="text-[20px] font-bold text-eldergo-blue">{weather.feelsLikeC}&deg;C</div>
                <div className="text-[13px] text-eldergo-muted">{t('routeWeatherFeelsLike')}</div>
              </div>
              <div className="rounded-xl bg-eldergo-bg px-3 py-3">
                <div className="text-[20px] font-bold text-eldergo-blue">{weather.windKmh}</div>
                <div className="text-[13px] text-eldergo-muted">{t('routeWeatherWind')}</div>
              </div>
              <div className="rounded-xl bg-eldergo-bg px-3 py-3">
                <div className="text-[20px] font-bold text-eldergo-blue">{weatherPeriodLabel()}</div>
                <div className="text-[13px] text-eldergo-muted">{t('routeWeatherRainPeriod')}</div>
              </div>
            </div>
          )}
          <div className="mt-4 rounded-xl bg-eldergo-green/10 px-4 py-3">
            <div className="text-[15px] font-semibold text-eldergo-navy mb-2">
              {t('routeWeatherSeniorTitle')}
            </div>
            <ul className="space-y-1">
              {seniorWeatherTips().map((tip) => (
                <li key={tip} className="flex gap-2 text-[14px] leading-relaxed text-eldergo-muted">
                  <span className="mt-2 h-1.5 w-1.5 rounded-full bg-eldergo-green flex-shrink-0" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
      </div>
    </div>
  );

  const buildShareableRouteLink = () => {
    if (!currentRoute) return window.location.href;
    return `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(currentRoute.origin_name)}&destination=${encodeURIComponent(currentRoute.destination_name)}&travelmode=transit`;
  };

  const mapEmbedSrc = currentRoute
    ? GOOGLE_MAPS_EMBED_KEY
      ? `https://www.google.com/maps/embed/v1/directions?key=${encodeURIComponent(GOOGLE_MAPS_EMBED_KEY)}&origin=${encodeURIComponent(currentRoute.origin_name)}&destination=${encodeURIComponent(currentRoute.destination_name)}&mode=transit`
      : `https://www.google.com/maps?output=embed&saddr=${encodeURIComponent(currentRoute.origin_name)}&daddr=${encodeURIComponent(currentRoute.destination_name)}&dirflg=r`
    : null;

  const showHint = (message: string) => {
    setActionHint(message);
    window.setTimeout(() => setActionHint(null), 2200);
  };

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

    try {
      const width = 1080;
      const padding = 64;
      const cardGap = 30;
      const contentWidth = width - padding * 2;
      const stepTitleWidth = contentWidth - 200;

      const preCanvas = document.createElement('canvas');
      const preCtx = preCanvas.getContext('2d');
      if (!preCtx) {
        showHint(t('routeSaveFailed'));
        return;
      }

      preCtx.font = 'bold 48px Poppins, sans-serif';
      const stepHeights = routeSteps.map((step) => {
        const titleLines = wrapLines(preCtx, step.title, stepTitleWidth);
        preCtx.font = '500 34px Poppins, sans-serif';
        const noteLines = wrapLines(preCtx, step.accessibility, contentWidth - 120);
        return {
          titleLines,
          noteLines,
          height: Math.max(280, 190 + titleLines.length * 52 + noteLines.length * 42)
        };
      });

      const totalStepsHeight = stepHeights.reduce((sum, item) => sum + item.height, 0) + cardGap * (routeSteps.length - 1);
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
      routeSteps.forEach((step, index) => {
        const { titleLines, noteLines, height } = stepHeights[index];
        drawRoundedRect(ctx, padding, y, contentWidth, height, 28);
        ctx.fillStyle = BRAND_COLORS.white;
        ctx.fill();

        ctx.fillStyle = step.color;
        ctx.fillRect(padding, y, 10, height);

        ctx.beginPath();
        ctx.arc(padding + 58, y + 58, 34, 0, Math.PI * 2);
        ctx.fillStyle = step.color;
        ctx.fill();
        ctx.fillStyle = BRAND_COLORS.white;
        ctx.font = '700 34px Poppins, sans-serif';
        ctx.fillText(String(step.step), padding + 47, y + 71);

        ctx.fillStyle = BRAND_COLORS.muted;
        ctx.font = '600 34px Poppins, sans-serif';
        ctx.fillText(`${t('routeStep')} ${step.step} ${t('routeOf')} ${routeSteps.length}`, padding + 125, y + 72);

        ctx.fillStyle = BRAND_COLORS.navy;
        ctx.font = '700 52px Poppins, sans-serif';
        let textY = y + 138;
        titleLines.forEach((line) => {
          ctx.fillText(line, padding + 58, textY, contentWidth - 110);
          textY += 54;
        });

        ctx.fillStyle = BRAND_COLORS.body;
        ctx.font = '500 40px Poppins, sans-serif';
        const durationText = step.distance
          ? `${t('routeDuration')}: ${step.duration} -${step.distance}`
          : `${t('routeDuration')}: ${step.duration}`;
        ctx.fillText(durationText, padding + 58, textY + 8, contentWidth - 110);

        const noteY = y + height - (noteLines.length * 42 + 44);
        drawRoundedRect(ctx, padding + 58, noteY, contentWidth - 116, noteLines.length * 42 + 24, 18);
        ctx.fillStyle = `${step.color}22`;
        ctx.fill();
        ctx.fillStyle = step.color;
        ctx.font = '600 34px Poppins, sans-serif';
        let noteTextY = noteY + 42;
        noteLines.forEach((line) => {
          ctx.fillText(line, padding + 88, noteTextY, contentWidth - 170);
          noteTextY += 42;
        });

        y += height + cardGap;
      });

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
        <div className="max-w-2xl mx-auto mt-6">
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
                  <h3 className="text-[28px] font-semibold text-eldergo-navy leading-tight">
                    {toLocationLabel(currentRoute.origin_name)}
                  </h3>
                  <div className="flex justify-center py-2">
                    <ArrowDown size={30} strokeWidth={2.8} className="text-eldergo-blue" />
                  </div>
                  <h3 className="text-[28px] font-semibold text-eldergo-navy leading-tight">
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
                <div className="text-[20px] font-bold text-eldergo-blue">{currentRoute?.duration_minutes ?? '-'} {t('routeMins')}</div>
                <div className="text-[14px] text-eldergo-muted">{t('routeTime')}</div>
              </div>
              <div>
                <div className="text-[20px] font-bold text-eldergo-blue">{currentRoute?.transfers ?? '-'}</div>
                <div className="text-[14px] text-eldergo-muted">{t('routeTransfers')}</div>
              </div>
              <div>
                <div className="text-[20px] font-bold text-eldergo-blue">{currentRoute?.walking_distance_meters ?? '-'}m</div>
                <div className="text-[14px] text-eldergo-muted">{t('routeWalk')}</div>
              </div>
            </div>
          </div>

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
                <button
                  onClick={() => scroll('left')}
                  className="absolute -left-2 sm:left-2 top-1/2 -translate-y-1/2 z-10 w-10 h-10 sm:w-12 sm:h-12 bg-white/95 backdrop-blur-sm border-2 border-eldergo-border rounded-full flex items-center justify-center hover:bg-white hover:border-eldergo-blue transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={currentStep === 0}
                >
                  <ChevronLeft size={20} strokeWidth={2.5} className="text-eldergo-navy sm:w-6 sm:h-6" />
                </button>

                <button
                  onClick={() => scroll('right')}
                  className="absolute -right-2 sm:right-2 top-1/2 -translate-y-1/2 z-10 w-10 h-10 sm:w-12 sm:h-12 bg-white/95 backdrop-blur-sm border-2 border-eldergo-border rounded-full flex items-center justify-center hover:bg-white hover:border-eldergo-blue transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={currentStep === routeSteps.length - 1}
                >
                  <ChevronRight size={20} strokeWidth={2.5} className="text-eldergo-navy sm:w-6 sm:h-6" />
                </button>

                <div className="overflow-hidden">
                  <div
                    className="flex transition-transform duration-300 ease-in-out"
                    style={{ transform: `translateX(-${currentStep * 100}%)` }}
                  >
                    {routeSteps.map((step) => {
                      const IconComponent = step.icon;
                      return (
                        <div
                          key={step.step}
                          className="w-full flex-shrink-0 px-6 sm:px-16 h-full"
                        >
                          <div
                            className="bg-white/95 backdrop-blur-sm p-5 sm:p-6 rounded-2xl shadow-xl border-l-4 min-h-[360px] sm:min-h-[400px] h-full overflow-hidden"
                            style={{ borderLeftColor: step.color }}
                          >
                            <div className="flex flex-col h-full">
                              <div className="flex items-center gap-3 mb-4">
                                <div
                                  className="w-10 h-10 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0"
                                  style={{
                                    backgroundColor: step.color,
                                    fontSize: `${16 * baseFontSize}px`
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

                              <div className="text-eldergo-muted mb-4" style={{ fontSize: `${16 * baseFontSize}px` }}>
                                {t('routeDuration')}: {step.duration}{step.distance ? ` -${step.distance}` : ''}
                              </div>

                              <div className="mt-auto px-4 py-3 rounded-lg" style={{ backgroundColor: `${step.color}20` }}>
                                <span className="font-medium break-words leading-snug" style={{ color: step.color, fontSize: `${14 * baseFontSize}px` }}>
                                  {step.accessibility}
                                </span>
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

          {weatherCard}
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
