import type { LucideIcon } from 'lucide-react';
import { Cloud, CloudLightning, CloudRain, CloudSun, Droplets, Sun, TrendingDown, TrendingUp } from 'lucide-react';
import type { DestinationWeather } from '../../services/weatherApi';
import type { Language, TranslationKey } from '../../i18n/translations';
import {
  buildLeaveWindowTimeline,
  buildWeatherChangeSummary,
  primarySeniorWeatherTip,
  simplifyWeatherCondition,
  weatherRiskBadgeLabel,
  type LeaveWindowTimelinePoint,
} from '../../utils/weatherDisplay';

export interface RouteWeatherCardProps {
  weather: DestinationWeather | null;
  weatherStatus: 'idle' | 'loading' | 'ready' | 'unavailable';
  plannedDestinationLabel: string;
  geocodedAreaLabel: string;
  showGeocodedHint: boolean;
  leavingLabel: string;
  departureTime: Date;
  language: Language;
  baseFontSize: number;
  t: (key: TranslationKey) => string;
}

function pickIconForCondition(condition: string, rainLikely: boolean): LucideIcon {
  const text = condition.toLowerCase();
  if (
    text.includes('storm') ||
    text.includes('thunder') ||
    text.includes('ribut') ||
    text.includes('petir')
  ) {
    return CloudLightning;
  }
  if (
    rainLikely ||
    text.includes('rain') ||
    text.includes('drizzle') ||
    text.includes('hujan') ||
    text.includes('renyai')
  ) {
    return CloudRain;
  }
  if (text.includes('clear') || text.includes('cerah') || text.includes('hot') || text.includes('panas')) {
    return Sun;
  }
  if (text.includes('cloud') || text.includes('berawan') || text.includes('mendung') || text.includes('fog') || text.includes('mist') || text.includes('kabut') || text.includes('jerebu')) {
    return Cloud;
  }
  return CloudSun;
}

function pickWeatherIcon(weather: DestinationWeather | null) {
  if (!weather) return Cloud;
  const description = `${weather.weatherMain} ${weather.weatherDescription}`;
  return pickIconForCondition(
    description,
    (weather.precipitationProbabilityPercent ?? 0) >= 40,
  );
}

function trendIcon(current: LeaveWindowTimelinePoint, previous: LeaveWindowTimelinePoint | null) {
  if (!previous || current.isDeparture) return null;
  const delta = current.temperatureC - previous.temperatureC;
  if (delta >= 0.5) return TrendingUp;
  if (delta <= -0.5) return TrendingDown;
  return null;
}

export default function RouteWeatherCard({
  weather,
  weatherStatus,
  plannedDestinationLabel,
  geocodedAreaLabel,
  showGeocodedHint,
  leavingLabel,
  departureTime,
  language,
  baseFontSize,
  t,
}: RouteWeatherCardProps) {
  const WeatherIcon = pickWeatherIcon(weather);
  const weatherRiskWord =
    weather && weather.riskLevel !== 'clear' && weather.riskLevel !== 'unavailable'
      ? weatherRiskBadgeLabel(weather, t)
      : null;

  const conditionText =
    weather && weatherStatus === 'ready'
      ? simplifyWeatherCondition(weather.weatherDescription || weather.weatherMain, language)
      : '';

  const timeline =
    weather && weatherStatus === 'ready'
      ? buildLeaveWindowTimeline(weather, language, departureTime)
      : [];

  const changeSummary = timeline.length > 0 ? buildWeatherChangeSummary(timeline, language) : '';

  const showSeniorTip =
    weatherStatus === 'loading' ||
    weatherStatus === 'unavailable' ||
    (weather && weather.riskLevel !== 'clear');

  const seniorTip =
    weatherStatus === 'loading'
      ? t('routeWeatherSeniorLoading')
      : weatherStatus !== 'ready' || !weather
        ? t('routeWeatherSeniorUnavailable')
        : primarySeniorWeatherTip(weather, language);

  return (
    <div className="bg-white/95 border-2 border-eldergo-border p-4 sm:p-5 rounded-2xl shadow-md mb-4">
      <div className="flex items-start gap-3">
        <div
          className="bg-eldergo-blue/15 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ width: `${44 * baseFontSize}px`, height: `${44 * baseFontSize}px` }}
        >
          <WeatherIcon size={22 * baseFontSize} strokeWidth={2.5} className="text-eldergo-blue" />
        </div>
        <div className="min-w-0 flex-1 pt-0.5">
          <h3
            className="font-semibold text-eldergo-navy leading-snug break-words"
            style={{ fontSize: `${18 * baseFontSize}px` }}
          >
            {plannedDestinationLabel}
          </h3>
          {weatherStatus === 'ready' && weather ? (
            <p className="text-eldergo-muted mt-1 leading-snug" style={{ fontSize: `${15 * baseFontSize}px` }}>
              <span className="font-medium text-eldergo-navy">{leavingLabel}</span>
              {weatherRiskWord ? (
                <span>
                  {' '}
                  · <span className="font-medium text-eldergo-navy">{weatherRiskWord}</span>
                </span>
              ) : null}
            </p>
          ) : (
            <p className="text-eldergo-muted mt-1" style={{ fontSize: `${14 * baseFontSize}px` }}>
              {t('routeWeatherForDeparture')}
            </p>
          )}
          {showGeocodedHint && (
            <p className="text-eldergo-muted mt-1 leading-snug" style={{ fontSize: `${12 * baseFontSize}px` }}>
              {t('routeWeatherGeocodedHint').replace('{name}', geocodedAreaLabel)}
            </p>
          )}
        </div>
      </div>

      {weatherStatus === 'ready' && weather && (
        <div className="mt-4 space-y-3">
          <div className="rounded-xl bg-eldergo-blue/10 px-4 py-3.5">
            <p
              className="font-semibold uppercase tracking-wide text-eldergo-blue/90"
              style={{ fontSize: `${12 * baseFontSize}px` }}
            >
              {t('routeWeatherLeaveTime')}
            </p>
            <p
              className="font-bold text-eldergo-blue tabular-nums leading-none tracking-tight mt-1"
              style={{ fontSize: `${34 * baseFontSize}px` }}
            >
              {weather.temperatureC}&deg;C
            </p>
            <p className="text-eldergo-navy mt-2 leading-snug" style={{ fontSize: `${15 * baseFontSize}px` }}>
              {t('routeWeatherFeelsLike')} {weather.feelsLikeC}&deg;C
              {conditionText ? (
                <span className="text-eldergo-muted">
                  {' '}
                  · {conditionText}
                </span>
              ) : null}
            </p>
          </div>

          {timeline.length > 0 && (
            <div className="rounded-xl border border-eldergo-border bg-[#F8FAFC] px-3 py-3 sm:px-4">
              <p className="font-semibold text-eldergo-navy leading-snug" style={{ fontSize: `${15 * baseFontSize}px` }}>
                {t('routeWeatherTrendTitle')}
              </p>
              <p className="text-eldergo-muted mt-0.5 mb-3 leading-snug" style={{ fontSize: `${13 * baseFontSize}px` }}>
                {t('routeWeatherLaterHint')}
              </p>
              <div className="flex flex-col gap-2">
                {timeline.map((point, index) => {
                  const previous = index > 0 ? timeline[index - 1] : null;
                  const Trend = trendIcon(point, previous);
                  const PointIcon = pickIconForCondition(point.condition, point.rainLikely);
                  return (
                    <div
                      key={`${point.hoursAfter}-${point.clockLabel}`}
                      className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 ${
                        point.isDeparture
                          ? 'border-eldergo-blue/40 bg-eldergo-blue/10'
                          : 'border-eldergo-border/70 bg-white'
                      }`}
                    >
                      <div
                        className="flex flex-shrink-0 items-center justify-center rounded-full bg-eldergo-blue/10"
                        style={{
                          width: `${40 * baseFontSize}px`,
                          height: `${40 * baseFontSize}px`,
                        }}
                      >
                        <PointIcon
                          size={20 * baseFontSize}
                          strokeWidth={2.5}
                          className="text-eldergo-blue"
                          aria-hidden
                        />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p
                          className="font-semibold text-eldergo-navy leading-snug"
                          style={{ fontSize: `${14 * baseFontSize}px` }}
                        >
                          {point.hoursAfterLabel}
                        </p>
                        <p
                          className="text-eldergo-muted tabular-nums leading-snug"
                          style={{ fontSize: `${13 * baseFontSize}px` }}
                        >
                          {point.clockLabel}
                        </p>
                      </div>
                      <div className="flex flex-shrink-0 flex-col items-end gap-0.5 text-right">
                        <div className="flex items-center gap-1">
                          {Trend && (
                            <Trend
                              size={14 * baseFontSize}
                              className={
                                point.temperatureC >= (previous?.temperatureC ?? point.temperatureC)
                                  ? 'text-eldergo-warning'
                                  : 'text-eldergo-blue'
                              }
                              strokeWidth={2.5}
                              aria-hidden
                            />
                          )}
                          <p
                            className="font-bold text-eldergo-navy tabular-nums leading-none"
                            style={{ fontSize: `${17 * baseFontSize}px` }}
                          >
                            {point.temperatureLabel}
                          </p>
                        </div>
                        <p
                          className="text-eldergo-muted leading-snug"
                          style={{ fontSize: `${13 * baseFontSize}px` }}
                        >
                          {point.condition}
                        </p>
                        {point.rainLikely && (
                          <span
                            className="inline-flex items-center gap-0.5 text-eldergo-blue"
                            style={{ fontSize: `${11 * baseFontSize}px` }}
                          >
                            <Droplets size={12 * baseFontSize} strokeWidth={2.5} aria-hidden />
                            {t('routeWeatherRainPossibleShort')}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              {changeSummary && (
                <p
                  className="mt-3 text-eldergo-navy font-medium leading-snug border-t border-eldergo-border/60 pt-2"
                  style={{ fontSize: `${13 * baseFontSize}px` }}
                >
                  {changeSummary}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {showSeniorTip && (
        <div className="mt-3 rounded-xl bg-eldergo-green/10 px-4 py-2.5">
          <p className="leading-snug text-eldergo-navy" style={{ fontSize: `${14 * baseFontSize}px` }}>
            {seniorTip}
          </p>
        </div>
      )}
    </div>
  );
}
