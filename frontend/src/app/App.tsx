import { useState } from 'react';
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

  // Shared navigation callbacks keep page switching wiring centralized.
  const navHandlers = {
    onNavigateToPlanning: () => setCurrentPage('planning'),
    onNavigateToStation: () => setCurrentPage('stationsHome'),
    onNavigateToHelp: () => setCurrentPage('help'),
    onNavigateToPreference: () => setCurrentPage('preference'),
    onShowChatbot: () => setShowChatbot(true)
  };

  const fontSizeClass =
    fontSize === 'extra_large' ? 'text-[24px]' : fontSize === 'large' ? 'text-[20px]' : 'text-base';

  return (
    <div className={`size-full ${fontSizeClass}`} style={{ fontFamily: 'Poppins' }}>
      {currentPage === 'planning' && (
        <PlanningPage
          {...navHandlers}
          onNavigateToPlanTime={() => setCurrentPage('planTime')}
          onNavigateToUseElderGo={() => setCurrentPage('useElderGo')}
        />
      )}
      {currentPage === 'planTime' && (
        <PlanYourTimePage
          {...navHandlers}
          onNavigateToRouteResult={() => setCurrentPage('routeResult')}
        />
      )}
      {currentPage === 'routeResult' && (
        <RouteResultPage
          {...navHandlers}
          onNavigateToPlanTime={() => setCurrentPage('planTime')}
        />
      )}
      {currentPage === 'stationsHome' && (
        <StationsHomePage
          {...navHandlers}
          onNavigateToStationDetail={() => setCurrentPage('stationDetail')}
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
          onNavigateToUseElderGo={() => setCurrentPage('useElderGo')}
          onNavigateToTicketGuide={() => setCurrentPage('ticketGuide')}
          onNavigateToConcessionGuide={() => setCurrentPage('concessionGuide')}
          onNavigateToPrivacyInfo={() => setCurrentPage('privacyInfo')}
        />
      )}
      {currentPage === 'useElderGo' && (
        <UseElderGoPage {...navHandlers} />
      )}
      {currentPage === 'ticketGuide' && (
        <TicketGuidePage
          {...navHandlers}
          onNavigateToHelp={() => setCurrentPage('help')}
        />
      )}
      {currentPage === 'concessionGuide' && (
        <ConcessionGuidePage
          {...navHandlers}
          onNavigateToHelp={() => setCurrentPage('help')}
        />
      )}
      {currentPage === 'privacyInfo' && (
        <PrivacyInfoPage
          {...navHandlers}
          onNavigateToHelp={() => setCurrentPage('help')}
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
    // App-wide state provider wraps all pages and chatbot sheet.
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
