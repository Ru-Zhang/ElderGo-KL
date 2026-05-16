import { CalendarClock, CalendarDays, Check, ChevronRight, Clock, Moon, Sun, Sunrise, Sunset } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState, type ChangeEvent, type ReactNode } from 'react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { useAppContext } from '../app/AppProvider';
import { getTranslation, TranslationKey } from '../i18n/translations';
import TimePicker12h from '../components/planning/TimePicker12h';
import {
  DEPARTURE_PRESETS,
  DeparturePreset,
  DepartureSelection,
  clampDatetimeLocal,
  isOutsideTransitServiceHours,
  datetimeLocalToIso,
  departureValueForApi,
  formatDateLocalDisplay,
  formatDepartureContextLabel,
  formatDeparturePreview,
  isDatetimeLocalInPast,
  joinDatetimeLocal,
  maxDateLocal,
  minDateLocal,
  normalizeDepartureKey,
  resolveDepartureDate,
  splitDatetimeLocal,
  toDatetimeLocalValue,
} from '../utils/departureTime';

interface PlanYourTimePageProps {
  onNavigateToPlanning: () => void;
  onRequestRoute: (apiDepartureTime: string) => void;
  onNavigateToStation: () => void;
  onNavigateToHelp: () => void;
  onNavigateToPreference: () => void;
  onShowChatbot: () => void;
}

const PRESET_LABEL_KEYS: Record<DeparturePreset, { label: TranslationKey; desc: TranslationKey }> = {
  now: { label: 'planTimeNow', desc: 'planTimeNowDesc' },
  morning_peak: { label: 'planTimeMorningPeak', desc: 'planTimeMorningPeakDesc' },
  midday: { label: 'planTimeMidday', desc: 'planTimeMiddayDesc' },
  evening_peak: { label: 'planTimeEveningPeak', desc: 'planTimeEveningPeakDesc' },
  night: { label: 'planTimeNight', desc: 'planTimeNightDesc' },
};

const PRESET_ICONS = {
  now: Clock,
  morning_peak: Sunrise,
  midday: Sun,
  evening_peak: Sunset,
  night: Moon,
} as const;

function isDeparturePreset(value: string): value is DeparturePreset {
  return DEPARTURE_PRESETS.includes(value as DeparturePreset);
}

function TouchPickerField({
  label,
  displayValue,
  inputType,
  value,
  min,
  max,
  onChange,
  baseFontSize,
  icon,
}: {
  label: string;
  displayValue: string;
  inputType: 'date' | 'time';
  value: string;
  min?: string;
  max?: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  baseFontSize: number;
  icon: ReactNode;
}) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  const openPicker = () => {
    const input = inputRef.current;
    if (!input) return;
    if (typeof input.showPicker === 'function') {
      try {
        input.showPicker();
        return;
      } catch {
        // showPicker can throw if not triggered by a user gesture
      }
    }
    input.focus();
    input.click();
  };

  return (
    <label
      htmlFor={inputId}
      onClick={openPicker}
      className="flex w-full min-h-[52px] cursor-pointer items-center gap-3 rounded-xl border-2 border-eldergo-border bg-white px-4 py-3 hover:border-eldergo-blue focus-within:border-eldergo-blue focus-within:ring-2 focus-within:ring-eldergo-blue/25"
    >
      <span className="shrink-0 text-eldergo-blue" aria-hidden>
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span
          className="block font-semibold uppercase tracking-wide text-eldergo-muted"
          style={{ fontSize: `${12 * baseFontSize}px` }}
        >
          {label}
        </span>
        <span
          className="mt-0.5 block font-semibold leading-snug text-eldergo-navy tabular-nums"
          style={{ fontSize: `${18 * baseFontSize}px` }}
        >
          {displayValue}
        </span>
      </span>
      <ChevronRight size={22} strokeWidth={2.5} className="shrink-0 text-eldergo-muted" aria-hidden />
      <input
        ref={inputRef}
        id={inputId}
        type={inputType}
        value={value}
        min={min}
        max={max}
        onChange={onChange}
        className="sr-only"
      />
    </label>
  );
}

function initialCustomDatetime(storedDeparture: string, preset: DeparturePreset): string {
  const normalized = normalizeDepartureKey(storedDeparture);
  if (typeof normalized === 'string' && normalized.includes('T')) {
    return clampDatetimeLocal(toDatetimeLocalValue(resolveDepartureDate(normalized)));
  }
  return clampDatetimeLocal(toDatetimeLocalValue(resolveDepartureDate(preset)));
}

export default function PlanYourTimePage({
  onNavigateToPlanning,
  onRequestRoute,
  onNavigateToStation,
  onNavigateToHelp,
  onNavigateToPreference,
  onShowChatbot,
}: PlanYourTimePageProps) {
  const {
    departureTime,
    fontSize,
    language,
    origin,
    destination,
    routeLoading,
    setRouteError,
  } = useAppContext();

  const normalizedStored = normalizeDepartureKey(departureTime);
  const storedIsIso = typeof normalizedStored === 'string' && normalizedStored.includes('T');
  const initialPreset: DepartureSelection = storedIsIso
    ? 'custom'
    : isDeparturePreset(String(normalizedStored))
      ? normalizedStored
      : 'now';

  const [selectedTime, setSelectedTime] = useState<DepartureSelection>(initialPreset);
  const [lastPreset, setLastPreset] = useState<DeparturePreset>(
    initialPreset === 'custom' ? 'now' : initialPreset,
  );
  const [customPickerOpen, setCustomPickerOpen] = useState(storedIsIso);
  const initialCustom = initialCustomDatetime(
    departureTime,
    initialPreset === 'custom' ? 'now' : initialPreset,
  );
  const [customDatetimeLocal, setCustomDatetimeLocal] = useState(initialCustom);
  const [committedCustomDatetime, setCommittedCustomDatetime] = useState(initialCustom);
  const [customTimeError, setCustomTimeError] = useState<string | null>(null);

  const customPreview = useMemo(
    () => formatDepartureContextLabel('custom', language, datetimeLocalToIso(committedCustomDatetime)),
    [committedCustomDatetime, language],
  );

  const baseFontSize = fontSize === 'extra_large' ? 1.5 : fontSize === 'large' ? 1.25 : 1;
  const t = (key: TranslationKey) => getTranslation(language, key);

  const summaryTime = useMemo(() => {
    if (selectedTime === 'custom') {
      return customPreview;
    }
    return formatDepartureContextLabel(selectedTime, language);
  }, [selectedTime, customPreview, language]);

  const customParts = splitDatetimeLocal(customDatetimeLocal);

  // #region agent log
  useEffect(() => {
    const presetLabels = DEPARTURE_PRESETS.map((preset) => {
      const resolved = resolveDepartureDate(preset).toISOString();
      return {
        preset,
        context: formatDepartureContextLabel(preset, language),
        full: formatDeparturePreview(preset, language),
        resolvedIso: resolved,
      };
    });
    fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
      body: JSON.stringify({
        sessionId: 'ce83c2',
        hypothesisId: 'H1-H2',
        location: 'PlanYourTimePage.tsx:preset-labels',
        message: 'preset short vs full labels',
        data: {
          presetLabels,
          selectedTime,
          summaryTime,
          customDatetimeLocal,
          customPreview,
          customIso: datetimeLocalToIso(customDatetimeLocal),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  }, [language, selectedTime, summaryTime, customDatetimeLocal, customPreview]);
  // #endregion

  const normalizeCustom = (value: string) => clampDatetimeLocal(value);
  const outsideServiceHours =
    selectedTime === 'custom' && isOutsideTransitServiceHours(committedCustomDatetime);

  const handleSelectPreset = (preset: DeparturePreset) => {
    setLastPreset(preset);
    setSelectedTime(preset);
    setCustomPickerOpen(false);
    setCustomTimeError(null);
    const next = normalizeCustom(toDatetimeLocalValue(resolveDepartureDate(preset)));
    setCustomDatetimeLocal(next);
    setCommittedCustomDatetime(next);
  };

  const handleSelectCustom = () => {
    const clamped = normalizeCustom(customDatetimeLocal);
    setCustomDatetimeLocal(clamped);
    setCommittedCustomDatetime(clamped);
    setSelectedTime('custom');
    setCustomPickerOpen(true);
    setCustomTimeError(isDatetimeLocalInPast(clamped) ? t('planTimeCustomMustBeFuture') : null);
    // #region agent log
    fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
      body: JSON.stringify({
        sessionId: 'ce83c2',
        hypothesisId: 'H3',
        location: 'PlanYourTimePage.tsx:handleSelectCustom',
        message: 'custom departure selected',
        data: { customDatetimeLocal: clamped, customPreview, runId: 'custom-select-fix' },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
  };

  const handleCancelCustom = () => {
    setSelectedTime(lastPreset);
    setCustomPickerOpen(false);
    setCustomTimeError(null);
    // #region agent log
    fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
      body: JSON.stringify({
        sessionId: 'ce83c2',
        hypothesisId: 'H3',
        location: 'PlanYourTimePage.tsx:handleCancelCustom',
        message: 'custom departure cancelled',
        data: { lastPreset, runId: 'custom-select-fix' },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
  };

  const handleCustomChange = (value: string) => {
    const clamped = normalizeCustom(value);
    setCustomDatetimeLocal(clamped);
    setCustomTimeError(isDatetimeLocalInPast(clamped) ? t('planTimeCustomMustBeFuture') : null);
  };

  const handleCustomDone = () => {
    const clamped = normalizeCustom(customDatetimeLocal);
    setCustomDatetimeLocal(clamped);
    setCommittedCustomDatetime(clamped);
    setSelectedTime('custom');
    setCustomPickerOpen(false);
    setCustomTimeError(isDatetimeLocalInPast(clamped) ? t('planTimeCustomMustBeFuture') : null);
    // #region agent log
    fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
      body: JSON.stringify({
        sessionId: 'ce83c2',
        hypothesisId: 'H5',
        location: 'PlanYourTimePage.tsx:handleCustomDone',
        message: 'custom time committed on Done',
        data: {
          draft: customDatetimeLocal,
          committed: clamped,
          summaryAfterDone: formatDepartureContextLabel('custom', language, datetimeLocalToIso(clamped)),
          runId: 'custom-done-fix',
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
  };

  const handleShowRoute = () => {
    if (!origin || !destination) {
      setRouteError(t('planTimeMissingPoints'));
      onNavigateToPlanning();
      return;
    }

    if (selectedTime === 'custom' && isDatetimeLocalInPast(committedCustomDatetime)) {
      setCustomTimeError(t('planTimeCustomMustBeFuture'));
      return;
    }

    const apiDepartureTime = departureValueForApi(
      selectedTime,
      selectedTime === 'custom' ? committedCustomDatetime : undefined,
    );
    // #region agent log
    fetch('http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ce83c2' },
      body: JSON.stringify({
        sessionId: 'ce83c2',
        hypothesisId: 'H4',
        location: 'PlanYourTimePage.tsx:handleShowRoute',
        message: 'departure sent to App route handler',
        data: {
          selectedTime,
          apiDepartureTime,
          summaryTime,
          customDatetimeLocal,
          runId: 'custom-select-fix',
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    setRouteError(null);
    onRequestRoute(apiDepartureTime);
  };

  const renderPresetRow = (preset: DeparturePreset) => {
    const IconComponent = PRESET_ICONS[preset];
    const isSelected = selectedTime === preset;
    const preview = formatDepartureContextLabel(preset, language);

    return (
      <button
        key={preset}
        type="button"
        onClick={() => handleSelectPreset(preset)}
        aria-pressed={isSelected}
        aria-label={`${t(PRESET_LABEL_KEYS[preset].label)}. ${t(PRESET_LABEL_KEYS[preset].desc)} ${preview}`}
        className={`w-full rounded-xl border-2 px-4 py-3.5 transition-all flex items-center gap-3 min-h-[72px] ${
          isSelected
            ? 'bg-white border-eldergo-blue shadow-sm'
            : 'bg-white/95 border-eldergo-border hover:border-eldergo-blue/40'
        }`}
      >
        <div
          className={`shrink-0 w-11 h-11 rounded-full flex items-center justify-center ${
            isSelected ? 'bg-eldergo-blue' : 'bg-eldergo-bg'
          }`}
        >
          <IconComponent
            size={22}
            strokeWidth={2.5}
            className={isSelected ? 'text-white' : 'text-eldergo-navy'}
          />
        </div>
        <div className="flex-1 min-w-0 text-left">
          <div
            className="font-semibold text-eldergo-navy leading-snug"
            style={{ fontSize: `${17 * baseFontSize}px` }}
          >
            {t(PRESET_LABEL_KEYS[preset].label)}
          </div>
          <div
            className="text-eldergo-blue font-semibold mt-0.5 tabular-nums"
            style={{ fontSize: `${15 * baseFontSize}px` }}
          >
            {preview}
          </div>
        </div>
        {isSelected && <Check size={22} strokeWidth={3} className="text-eldergo-blue shrink-0" />}
      </button>
    );
  };

  return (
    <div className="min-h-screen relative" style={{ fontFamily: 'Poppins' }}>
      <div
        className="fixed inset-0 z-0 bg-cover bg-center"
        style={{
          backgroundImage: 'url(/background-elder.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="absolute inset-0 bg-white/40" />
      </div>
      <div className="relative z-10">
        <TopBar onLogoClick={onNavigateToPlanning} />

        <main className="pt-20 pb-36 px-4 sm:px-6">
          <div className="max-w-2xl mx-auto mt-4">
            <h2
              className="font-semibold text-eldergo-navy mb-1 leading-tight"
              style={{ fontSize: `${24 * baseFontSize}px` }}
            >
              {t('planTimeTitle')}
            </h2>
            <p
              className="text-eldergo-muted mb-4 leading-relaxed"
              style={{ fontSize: `${14 * baseFontSize}px` }}
            >
              {t('planTimeTransitHoursNote')}
            </p>

            <div className="space-y-2.5 mb-4">
              {DEPARTURE_PRESETS.map((preset) => renderPresetRow(preset))}
            </div>

            <button
              type="button"
              onClick={() => {
                if (selectedTime === 'custom') {
                  if (customPickerOpen) {
                    setCustomPickerOpen(false);
                  } else {
                    setCustomDatetimeLocal(committedCustomDatetime);
                    setCustomPickerOpen(true);
                  }
                } else {
                  handleSelectCustom();
                }
              }}
              aria-pressed={selectedTime === 'custom'}
              aria-label={
                selectedTime === 'custom'
                  ? `${t('planTimeCustomExact')}. ${summaryTime}`
                  : `${t('planTimeCustomExact')}. ${t('planTimeCustomExactDesc')}`
              }
              className={`w-full rounded-xl border-2 px-4 py-3.5 transition-all flex items-center gap-3 min-h-[72px] mb-2.5 ${
                selectedTime === 'custom'
                  ? 'bg-white border-eldergo-blue shadow-sm'
                  : 'bg-white/95 border-eldergo-border hover:border-eldergo-blue/40'
              }`}
            >
              <div
                className={`shrink-0 w-11 h-11 rounded-full flex items-center justify-center ${
                  selectedTime === 'custom' ? 'bg-eldergo-blue' : 'bg-eldergo-bg'
                }`}
              >
                <CalendarClock
                  size={22}
                  strokeWidth={2.5}
                  className={selectedTime === 'custom' ? 'text-white' : 'text-eldergo-navy'}
                />
              </div>
              <div className="flex-1 min-w-0 text-left">
                <div
                  className="font-semibold text-eldergo-navy leading-snug"
                  style={{ fontSize: `${17 * baseFontSize}px` }}
                >
                  {t('planTimeCustomExact')}
                </div>
                {selectedTime === 'custom' ? (
                  <p
                    className="mt-0.5 font-semibold leading-snug text-eldergo-blue tabular-nums"
                    style={{ fontSize: `${15 * baseFontSize}px` }}
                  >
                    {customPreview}
                  </p>
                ) : (
                  <p
                    className="mt-0.5 leading-snug text-eldergo-muted"
                    style={{ fontSize: `${14 * baseFontSize}px` }}
                  >
                    {t('planTimeCustomExactDesc')}
                  </p>
                )}
              </div>
              {selectedTime === 'custom' && (
                <Check size={22} strokeWidth={3} className="text-eldergo-blue shrink-0" />
              )}
            </button>

            {selectedTime === 'custom' && customPickerOpen && (
              <div className="mb-4 space-y-3 rounded-xl border-2 border-eldergo-border bg-white p-4 shadow-sm max-w-full">
                <TouchPickerField
                  label={t('planTimeCustomDate')}
                  displayValue={formatDateLocalDisplay(customParts.date, language)}
                  inputType="date"
                  value={customParts.date}
                  min={minDateLocal()}
                  max={maxDateLocal()}
                  onChange={(e) => handleCustomChange(joinDatetimeLocal(e.target.value, customParts.time))}
                  baseFontSize={baseFontSize}
                  icon={<CalendarDays size={24} strokeWidth={2.5} />}
                />
                <TimePicker12h
                  label={t('planTimeCustomTime')}
                  date={customParts.date}
                  value={customParts.time}
                  language={language}
                  baseFontSize={baseFontSize}
                  icon={<Clock size={24} strokeWidth={2.5} />}
                  onChange={(time) => handleCustomChange(joinDatetimeLocal(customParts.date, time))}
                />
                {customTimeError && (
                  <p
                    className="text-eldergo-warning font-medium leading-relaxed"
                    style={{ fontSize: `${14 * baseFontSize}px` }}
                    role="alert"
                  >
                    {customTimeError}
                  </p>
                )}
                {outsideServiceHours && !customTimeError && (
                  <p
                    className="text-eldergo-muted leading-relaxed"
                    style={{ fontSize: `${14 * baseFontSize}px` }}
                    role="status"
                  >
                    {t('planTimeOutsideServiceHours')}
                  </p>
                )}
                <div className="flex flex-col gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleCustomDone}
                    className="min-h-12 w-full rounded-xl border-2 border-eldergo-blue bg-eldergo-blue px-4 py-3 font-semibold text-white hover:bg-eldergo-blue/90"
                    style={{ fontSize: `${16 * baseFontSize}px` }}
                  >
                    {t('planTimeCustomDone')}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelCustom}
                    className="min-h-12 w-full rounded-xl border-2 border-eldergo-border px-4 py-3 font-semibold text-eldergo-muted hover:border-eldergo-warning/50 hover:text-eldergo-navy"
                    style={{ fontSize: `${15 * baseFontSize}px` }}
                  >
                    {t('planTimeCancelCustom')}
                  </button>
                </div>
              </div>
            )}

            <p
              className="text-center font-semibold text-eldergo-navy mb-4 leading-relaxed px-1"
              style={{ fontSize: `${17 * baseFontSize}px` }}
              role="status"
            >
              {t('planTimeLeavingAt').replace('{time}', summaryTime)}
            </p>

            <button
              type="button"
              onClick={handleShowRoute}
              disabled={routeLoading || Boolean(customTimeError)}
              className="w-full bg-eldergo-warning hover:bg-eldergo-warning-dark text-white font-semibold py-4 rounded-xl transition-colors shadow-lg disabled:opacity-60"
              style={{ fontSize: `${20 * baseFontSize}px` }}
            >
              {routeLoading ? t('planTimeFindingRoute') : t('planTimeShowRoute')}
            </button>
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
