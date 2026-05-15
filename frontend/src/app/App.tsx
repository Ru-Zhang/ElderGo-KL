import { useEffect, useLayoutEffect, useState } from 'react';
import { AppProvider, useAppContext } from './AppProvider';
import PlanningPage from '../pages/PlanningPage';
import PlanYourTimePage from '../pages/PlanYourTimePage';
import RouteResultPage from '../pages/RouteResultPage';
import StationsHomePage from '../pages/StationsHomePage';
import StationDetailPage from '../pages/StationDetailPage';
import HelpPage from '../pages/HelpPage';
import UseElderGoPage from '../pages/UseElderGoPage';
import TicketGuidePage from '../pages/TicketGuidePage';
import ConcessionGuidePage from '../pages/ConcessionGuidePage';
import PrivacyInfoPage from '../pages/PrivacyInfoPage';
import PreferencePage from '../pages/PreferencePage';
import AIChatbotSheet from '../components/chatbot/AIChatbotSheet';
import { resetPageScroll } from '../utils/resetPageScroll';

type PageType =
  | 'planning'
  | 'planTime'
  | 'routeResult'
  | 'stationsHome'
  | 'stationDetail'
  | 'help'
  | 'useElderGo'
  | 'ticketGuide'
  | 'concessionGuide'
  | 'privacyInfo'
  | 'preference';

function AppContent() {
  const [currentPage, setCurrentPage] = useState<PageType>('planning');
  const [showChatbot, setShowChatbot] = useState(false);
  const { fontSize } = useAppContext();

  const navigateToPage = (nextPage: PageType) => {
    setCurrentPage(nextPage);
  };

  useLayoutEffect(() => {
    resetPageScroll();
  }, [currentPage]);

  useEffect(() => {
    resetPageScroll();
    requestAnimationFrame(() => resetPageScroll());
  }, [currentPage]);

  const navHandlers = {
    onNavigateToPlanning: () => navigateToPage('planning'),
    onNavigateToStation: () => navigateToPage('stationsHome'),
    onNavigateToHelp: () => navigateToPage('help'),
    onNavigateToPreference: () => navigateToPage('preference'),
    onShowChatbot: () => setShowChatbot(true),
  };

  const fontSizeClass =
    fontSize === 'extra_large' ? 'text-[24px]' : fontSize === 'large' ? 'text-[20px]' : 'text-base';

  return (
    <div
      className={`size-full min-w-0 max-w-full overflow-x-hidden ${fontSizeClass}`}
      style={{ fontFamily: 'Poppins' }}
    >
      {currentPage === 'planning' && (
        <PlanningPage
          {...navHandlers}
          onNavigateToPlanTime={() => navigateToPage('planTime')}
          onNavigateToUseElderGo={() => navigateToPage('useElderGo')}
        />
      )}
      {currentPage === 'planTime' && (
        <PlanYourTimePage
          {...navHandlers}
          onNavigateToRouteResult={() => navigateToPage('routeResult')}
        />
      )}
      {currentPage === 'routeResult' && (
        <RouteResultPage
          {...navHandlers}
          onNavigateToPlanTime={() => navigateToPage('planTime')}
        />
      )}
      {currentPage === 'stationsHome' && (
        <StationsHomePage
          {...navHandlers}
          onNavigateToStationDetail={() => navigateToPage('stationDetail')}
        />
      )}
      {currentPage === 'stationDetail' && (
        <StationDetailPage
          {...navHandlers}
        />
      )}
      {currentPage === 'help' && (
        <HelpPage
          {...navHandlers}
          onNavigateToUseElderGo={() => navigateToPage('useElderGo')}
          onNavigateToTicketGuide={() => navigateToPage('ticketGuide')}
          onNavigateToConcessionGuide={() => navigateToPage('concessionGuide')}
          onNavigateToPrivacyInfo={() => navigateToPage('privacyInfo')}
        />
      )}
      {currentPage === 'useElderGo' && (
        <UseElderGoPage {...navHandlers} />
      )}
      {currentPage === 'ticketGuide' && (
        <TicketGuidePage
          {...navHandlers}
          onNavigateToHelp={() => navigateToPage('help')}
        />
      )}
      {currentPage === 'concessionGuide' && (
        <ConcessionGuidePage
          {...navHandlers}
          onNavigateToHelp={() => navigateToPage('help')}
        />
      )}
      {currentPage === 'privacyInfo' && (
        <PrivacyInfoPage
          {...navHandlers}
          onNavigateToHelp={() => navigateToPage('help')}
        />
      )}
      {currentPage === 'preference' && (
        <PreferencePage {...navHandlers} />
      )}

      <AIChatbotSheet
        isOpen={showChatbot}
        onClose={() => setShowChatbot(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
