import * as React from 'react';
import { useEffect, useState } from 'react';
import {
  Accessibility,
  AlertTriangle,
  Check,
  Clock,
  HelpCircle,
  Loader2,
  MapPin,
  TrainFront,
  X,
} from 'lucide-react';
import type { LocationDetail } from '../../types/locations';
import { resolveStationDetailByName } from '../../services/resolveStationDetail';
import { parseHoursSummary } from '../../utils/hoursParser';
import { LineBadge } from '../../utils/lineBadge';
import { prepareFacilitiesForDisplay } from '../../utils/facilityPriority';
import FacilityChips from './FacilityChips';
import { useAppContext } from '../../app/AppProvider';
import { HoursDisplay } from './HoursDisplay';

interface StationDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Station display name pulled from the route step (e.g. "KL Sentral"). */
  stationName: string | null;
  baseFontSize: number;
  t: (key: string) => string;
}

type LoadStatus = 'idle' | 'loading' | 'ready' | 'not_found' | 'error';

/**
 * Lightweight popup that mirrors the most important sections of the station
 * detail page (accessibility, routes, address, hours, facilities) so users
 * can peek at a stop without leaving the route results screen.
 *
 * It performs its own backend lookup using `searchLocations` to resolve a
 * station name into a location_id, then fetches the full detail. If the
 * search returns multiple matches we pick the closest case-insensitive
 * exact match and fall back to the first hit.
 */
export function StationDetailModal({
  isOpen,
  onClose,
  stationName,
  baseFontSize,
  t,
}: StationDetailModalProps) {
  const { language } = useAppContext();
  const [status, setStatus] = useState<LoadStatus>('idle');
  const [detail, setDetail] = useState<LocationDetail | null>(null);
  const [showLastTrains, setShowLastTrains] = useState(false);

  // Reset state every time we open the modal for a new station so previous
  // content doesn't flash through during the next fetch cycle.
  useEffect(() => {
    if (!isOpen || !stationName) return;

    let cancelled = false;
    setStatus('loading');
    setDetail(null);
    setShowLastTrains(false);

    (async () => {
      try {
        const fetched = await resolveStationDetailByName(stationName);
        if (cancelled) return;
        if (!fetched) {
          setStatus('not_found');
          return;
        }
        setDetail(fetched);
        setStatus('ready');
      } catch {
        if (cancelled) return;
        setStatus('error');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isOpen, stationName]);

  // Close on ESC for keyboard users.
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const accessibilityStatus = detail?.accessibility_status ?? 'unknown';
  const accessibilityChip =
    accessibilityStatus === 'supported'
      ? {
          bg: 'bg-eldergo-green/15',
          fg: 'text-eldergo-green',
          Icon: Check,
          label: t('accessibilityChipSupported'),
        }
      : accessibilityStatus === 'not_supported'
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

  const facilities = prepareFacilitiesForDisplay(detail?.station_facilities ?? []);
  const address = detail?.station_address ?? null;
  const parsedHours = parseHoursSummary(detail?.station_hours_summary);
  const facilitySourceUrl = detail?.facility_source_url ?? null;
  const dataSourcesLine = [
    ...(detail?.source_list ?? []),
    facilitySourceUrl ? 'mrt.com.my' : null,
  ].filter(Boolean) as string[];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={t('stationModalAria')}
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />

      <div
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[88vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between px-6 py-5 border-b border-eldergo-border bg-white">
          <div className="flex-1 min-w-0 pr-4">
            <p
              className="text-eldergo-muted font-semibold uppercase tracking-wide mb-1"
              style={{ fontSize: `${12 * baseFontSize}px`, letterSpacing: '0.06em' }}
            >
              {t('stationModalTitle')}
            </p>
            <h2
              className="font-semibold text-eldergo-navy leading-tight break-words"
              style={{ fontSize: `${24 * baseFontSize}px` }}
            >
              {detail?.name ?? stationName ?? ''}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex-shrink-0 w-11 h-11 rounded-full bg-eldergo-bg hover:bg-eldergo-border text-eldergo-navy flex items-center justify-center transition-colors"
            aria-label={t('stationModalClose')}
          >
            <X size={22} strokeWidth={2.6} />
          </button>
        </div>

        <div className="overflow-y-auto px-6 py-6">
          {status === 'loading' && (
            <div
              className="flex flex-col items-center justify-center gap-3 py-14 text-eldergo-muted"
              style={{ fontSize: `${16 * baseFontSize}px` }}
            >
              <Loader2 className="animate-spin text-eldergo-blue" size={32} strokeWidth={2.4} />
              <span>{t('stationModalLoading')}</span>
            </div>
          )}

          {status === 'not_found' && (
            <div
              className="flex flex-col items-center text-center gap-3 py-12 text-eldergo-muted"
              style={{ fontSize: `${16 * baseFontSize}px` }}
            >
              <AlertTriangle className="text-eldergo-warning" size={32} strokeWidth={2.4} />
              <span>{t('stationModalNotFound')}</span>
            </div>
          )}

          {status === 'error' && (
            <div
              className="flex flex-col items-center text-center gap-3 py-12 text-eldergo-warning"
              style={{ fontSize: `${16 * baseFontSize}px` }}
            >
              <AlertTriangle size={32} strokeWidth={2.4} />
              <span>{t('stationModalError')}</span>
            </div>
          )}

          {status === 'ready' && detail && (
            <div className="space-y-5">
              <ModalRow
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
              </ModalRow>

              <div className="h-px bg-eldergo-border" />

              <ModalRow Icon={TrainFront} label={t('routes')} baseFontSize={baseFontSize}>
                {detail.routes && detail.routes.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {detail.routes.map((r) => (
                      <LineBadge key={r} name={r} baseFontSize={baseFontSize} />
                    ))}
                  </div>
                ) : (
                  <span
                    className="text-eldergo-muted font-medium"
                    style={{ fontSize: `${16 * baseFontSize}px` }}
                  >
                    {t('notYetVerified')}
                  </span>
                )}
              </ModalRow>

              {address && (
                <>
                  <div className="h-px bg-eldergo-border" />
                  <ModalRow Icon={MapPin} label={t('stationAddress')} baseFontSize={baseFontSize}>
                    <span
                      className="text-eldergo-navy font-medium"
                      style={{ fontSize: `${16 * baseFontSize}px`, lineHeight: 1.4 }}
                    >
                      {address}
                    </span>
                  </ModalRow>
                </>
              )}

              {parsedHours && (
                <>
                  <div className="h-px bg-eldergo-border" />
                  <ModalRow Icon={Clock} label={t('stationHours')} baseFontSize={baseFontSize}>
                    <HoursDisplay
                      parsed={parsedHours}
                      baseFontSize={baseFontSize}
                      t={t}
                      language={language}
                      isExpanded={showLastTrains}
                      onToggle={() => setShowLastTrains((v) => !v)}
                    />
                  </ModalRow>
                </>
              )}

              {facilities.length > 0 && (
                <>
                  <div className="h-px bg-eldergo-border" />
                  <div>
                    <p
                      className="font-semibold text-eldergo-muted mb-3 uppercase tracking-wide"
                      style={{ fontSize: `${12 * baseFontSize}px`, letterSpacing: '0.06em' }}
                    >
                      {t('stationFacilities')}
                    </p>
                    <FacilityChips
                      items={facilities}
                      language={language}
                      baseFontSize={baseFontSize}
                      compact
                    />
                  </div>
                </>
              )}

              {dataSourcesLine.length > 0 && (
                <>
                  <div className="h-px bg-eldergo-border" />
                  <div
                    className="text-eldergo-muted flex flex-wrap items-center gap-2"
                    style={{ fontSize: `${12 * baseFontSize}px` }}
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
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface ModalRowProps {
  Icon: typeof Check;
  label: string;
  baseFontSize: number;
  children: React.ReactNode;
}

/** Same visual layout as the InfoRow on the station detail page so the
 *  modal feels familiar to users who've seen the full page before. */
function ModalRow({ Icon, label, baseFontSize, children }: ModalRowProps) {
  return (
    <div className="flex gap-3 items-start">
      <div
        className="flex-shrink-0 rounded-full bg-eldergo-blue/10 flex items-center justify-center"
        style={{
          width: 36 * baseFontSize,
          height: 36 * baseFontSize,
        }}
      >
        <Icon className="text-eldergo-blue" size={20 * baseFontSize} strokeWidth={2.4} />
      </div>
      <div className="flex-1 min-w-0 pt-1">
        <p
          className="font-semibold text-eldergo-muted mb-1.5 uppercase tracking-wide"
          style={{ fontSize: `${11 * baseFontSize}px`, letterSpacing: '0.06em' }}
        >
          {label}
        </p>
        {children}
      </div>
    </div>
  );
}
