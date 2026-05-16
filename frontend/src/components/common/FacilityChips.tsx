import type { LucideIcon } from 'lucide-react';
import { pickFacilityIcon } from '../../utils/facilityIcons';
import { translateFacility } from '../../utils/dataI18n';
import { getFacilityTier, type FacilityTier } from '../../utils/facilityPriority';
import { getTranslation, type Language, type TranslationKey } from '../../i18n/translations';

const TIER_GROUP_KEYS: Record<FacilityTier, TranslationKey> = {
  1: 'facilityGroupMobility',
  2: 'facilityGroupEssentials',
  3: 'facilityGroupMore',
};

interface FacilityChipsProps {
  items: string[];
  language: Language;
  baseFontSize?: number;
  /** Slightly smaller chips for modals */
  compact?: boolean;
}

function chipStyles(tier: FacilityTier): { chip: string; icon: string } {
  if (tier === 1) {
    return {
      chip: 'border-eldergo-blue bg-eldergo-blue text-white font-semibold shadow-sm',
      icon: 'text-white flex-shrink-0',
    };
  }
  if (tier === 2) {
    return {
      chip: 'border-eldergo-blue/60 bg-eldergo-blue/10 text-eldergo-navy font-semibold',
      icon: 'text-eldergo-blue-dark flex-shrink-0',
    };
  }
  return {
    chip: 'border-eldergo-border bg-white text-eldergo-navy font-medium',
    icon: 'text-eldergo-blue flex-shrink-0',
  };
}

function FacilityChip({
  label,
  Icon,
  tier,
  baseFontSize,
  compact,
}: {
  label: string;
  Icon: LucideIcon;
  tier: FacilityTier;
  baseFontSize: number;
  compact: boolean;
}) {
  const { chip, icon } = chipStyles(tier);
  const iconSize = (compact ? 16 : 18) * baseFontSize;
  const fontSize = (compact ? 13 : 14) * baseFontSize;

  return (
    <span
      className={`flex h-full min-h-[44px] w-full items-center gap-2 rounded-xl border-2 px-3 py-2.5 ${chip}`}
      style={{ fontSize: `${fontSize}px` }}
    >
      <Icon size={iconSize} className={icon} strokeWidth={tier === 3 ? 2.2 : 2.5} aria-hidden />
      <span className="min-w-0 flex-1 leading-snug line-clamp-2 text-left">{label}</span>
    </span>
  );
}

export default function FacilityChips({
  items,
  language,
  baseFontSize = 1,
  compact = false,
}: FacilityChipsProps) {
  const t = (key: TranslationKey) => getTranslation(language, key);
  const tiers: FacilityTier[] = [1, 2, 3];
  const grouped = tiers
    .map((tier) => ({
      tier,
      items: items.filter((item) => getFacilityTier(item) === tier),
    }))
    .filter((group) => group.items.length > 0);

  if (grouped.length === 0) return null;

  const groupTitleSize = (compact ? 11 : 12) * baseFontSize;

  return (
    <div className="space-y-4" role="list" aria-label={t('stationFacilities')}>
      {grouped.map(({ tier, items: tierItems }) => (
        <section key={tier} role="listitem">
          <p
            className="mb-2 font-semibold uppercase tracking-wide text-eldergo-muted"
            style={{ fontSize: `${groupTitleSize}px`, letterSpacing: '0.05em' }}
          >
            {t(TIER_GROUP_KEYS[tier])}
          </p>
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {tierItems.map((item) => {
              const localizedLabel = translateFacility(item, language);
              const Icon = pickFacilityIcon(item);
              const spanClass =
                localizedLabel.length > 22 ? 'col-span-2 sm:col-span-2' : 'col-span-1';

              return (
                <li key={item} className={spanClass}>
                  <FacilityChip
                    label={localizedLabel}
                    Icon={Icon}
                    tier={tier}
                    baseFontSize={baseFontSize}
                    compact={compact}
                  />
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
