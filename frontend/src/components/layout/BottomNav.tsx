import type { ReactNode } from 'react';
import { Map, Sliders, Bot, HelpCircle, Train } from 'lucide-react';
import { useAppContext } from '../../app/AppProvider';
import { getTranslation } from '../../i18n/translations';

/** Reserve this space at the bottom of scrollable pages so content clears the fixed nav. */
export const BOTTOM_NAV_CLEARANCE = '6.25rem';

interface BottomNavProps {
  activeTab?: string;
  onChatbotClick?: () => void;
  onStationClick?: () => void;
  onPlanningClick?: () => void;
  onHelpClick?: () => void;
  onPreferenceClick?: () => void;
}

interface NavItemProps {
  active: boolean;
  label?: string;
  onClick?: () => void;
  iconBoxClass?: string;
  labelFontPx: number;
  labelSlotMinHeightPx: number;
  'aria-label'?: string;
  children: ReactNode;
}

const LABEL_SLOT_CLASS =
  'block w-full min-w-0 overflow-hidden text-center font-medium leading-none whitespace-nowrap';

function NavItem({
  active,
  label,
  onClick,
  iconBoxClass = 'h-10 w-10',
  labelFontPx,
  labelSlotMinHeightPx,
  'aria-label': ariaLabel,
  children,
}: NavItemProps) {
  const labelStyle = {
    fontFamily: 'Poppins',
    fontSize: `${labelFontPx}px`,
    minHeight: `${labelSlotMinHeightPx}px`,
    maxHeight: `${labelSlotMinHeightPx}px`,
  };

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={ariaLabel ?? label}
      className={`flex min-h-[4.75rem] w-full min-w-0 flex-col items-center justify-end gap-0.5 overflow-hidden px-0 pb-1 ${
        active ? 'text-eldergo-blue' : 'text-eldergo-navy'
      }`}
    >
      <div className={`flex flex-shrink-0 items-center justify-center ${iconBoxClass}`}>
        {children}
      </div>
      {label ? (
        <span className={LABEL_SLOT_CLASS} style={labelStyle}>
          {label}
        </span>
      ) : (
        <span className={LABEL_SLOT_CLASS} style={labelStyle} aria-hidden>
          {'\u00A0'}
        </span>
      )}
    </button>
  );
}

export default function BottomNav({
  activeTab = 'home',
  onChatbotClick,
  onStationClick,
  onPlanningClick,
  onHelpClick,
  onPreferenceClick,
}: BottomNavProps) {
  const { language, fontSize } = useAppContext();
  const t = (key: string) => getTranslation(language, key as any);
  const navScale = fontSize === 'extra_large' ? 1.1 : fontSize === 'large' ? 1.05 : 1;
  const iconSize = Math.round(30 * navScale);
  const chatbotIconSize = Math.round(32 * navScale);
  const chatbotCirclePx = Math.round(48 * navScale);
  const labelFontPx = Math.round(13 * navScale);
  const labelSlotMinHeightPx = Math.round(18 * navScale);
  const navItemProps = { labelFontPx, labelSlotMinHeightPx };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t-2 border-eldergo-border bg-white px-1 py-2 safe-area-pb sm:px-1.5">
      <div className="mx-auto grid max-w-5xl grid-cols-5 items-end gap-0">
        <NavItem active={activeTab === 'planning'} label={t('planning')} onClick={onPlanningClick} {...navItemProps}>
          <Map size={iconSize} strokeWidth={activeTab === 'planning' ? 2.5 : 2} />
        </NavItem>

        <NavItem active={activeTab === 'station'} label={t('stations')} onClick={onStationClick} {...navItemProps}>
          <Train size={iconSize} strokeWidth={activeTab === 'station' ? 2.5 : 2} />
        </NavItem>

        <NavItem
          active={false}
          onClick={onChatbotClick}
          iconBoxClass="flex-shrink-0"
          aria-label={t('chatbot')}
          {...navItemProps}
        >
          <div
            className="flex items-center justify-center rounded-full bg-eldergo-blue shadow-md"
            style={{ width: chatbotCirclePx, height: chatbotCirclePx }}
          >
            <Bot size={chatbotIconSize} strokeWidth={2.5} className="text-white" />
          </div>
        </NavItem>

        <NavItem
          active={activeTab === 'preference'}
          label={t('preference')}
          onClick={onPreferenceClick}
          {...navItemProps}
        >
          <Sliders size={iconSize} strokeWidth={activeTab === 'preference' ? 2.5 : 2} />
        </NavItem>

        <NavItem active={activeTab === 'help'} label={t('help')} onClick={onHelpClick} {...navItemProps}>
          <HelpCircle size={iconSize} strokeWidth={activeTab === 'help' ? 2.5 : 2} />
        </NavItem>
      </div>
    </div>
  );
}
