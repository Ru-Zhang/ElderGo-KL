import type { ReactNode } from 'react';
import TopBar from '../layout/TopBar';
import BottomNav, { BOTTOM_NAV_CLEARANCE } from '../layout/BottomNav';

export interface HelpPageShellProps {
  children: ReactNode;
  onLogoClick?: () => void;
  activeTab?: string;
  onChatbotClick?: () => void;
  onStationClick?: () => void;
  onPlanningClick?: () => void;
  onHelpClick?: () => void;
  onPreferenceClick?: () => void;
}

export default function HelpPageShell({
  children,
  onLogoClick,
  activeTab = 'help',
  onChatbotClick,
  onStationClick,
  onPlanningClick,
  onHelpClick,
  onPreferenceClick,
}: HelpPageShellProps) {
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
        <div className="absolute inset-0 bg-gradient-to-b from-white/50 via-white/45 to-white/50" />
        <div
          className="absolute bottom-0 left-0 right-0 h-96 bg-bottom bg-no-repeat bg-contain"
          style={{
            backgroundImage: 'url(/watermark-elder.jpg)',
            opacity: '0.12',
          }}
        />
      </div>
      <div className="relative z-10">
        <TopBar onLogoClick={onLogoClick} />
        <main
          className="pt-20 px-5 sm:px-6"
          style={{ paddingBottom: `calc(${BOTTOM_NAV_CLEARANCE} + 0.5rem)` }}
        >
          <div className="max-w-2xl mx-auto space-y-5">{children}</div>
        </main>
        <BottomNav
          activeTab={activeTab}
          onChatbotClick={onChatbotClick}
          onStationClick={onStationClick}
          onHelpClick={onHelpClick}
          onPlanningClick={onPlanningClick}
          onPreferenceClick={onPreferenceClick}
        />
      </div>
    </div>
  );
}
