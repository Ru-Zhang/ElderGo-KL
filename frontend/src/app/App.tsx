import { lazy, Suspense, useEffect, useState } from 'react';
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
import ChatbotLoadingShell from '../components/chatbot/ChatbotLoadingShell';
import { getTranslation } from '../i18n/translations';
import { debugLog } from '../utils/debugLog';

const AIChatbotSheet = lazy(() => import('../components/chatbot/AIChatbotSheet'));
import { getLocationDetail } from '../services/locationsApi';
import { ChatAction } from '../types/ai';
import { recommendRoute } from '../services/routesApi';

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
  const [routeInitialViewMode, setRouteInitialViewMode] = useState<'text' | 'map'>('text');
  const {
    language,
    fontSize,
    anonymousUserId,
    preferences,
    setSelectedStation,
    setOrigin,
    setDestination,
    setDepartureTime,
    setCurrentRoute,
    setRouteLoading,
    setRouteError
  } = useAppContext();
  const [stationsSearchQuery, setStationsSearchQuery] = useState('');

  useEffect(() => {
    void import('../components/chatbot/AIChatbotSheet');
  }, []);

  // Shared navigation callbacks keep page switching wiring centralized.
  const navHandlers = {
    onNavigateToPlanning: () => setCurrentPage('planning'),
    onNavigateToStation: () => setCurrentPage('stationsHome'),
    onNavigateToHelp: () => setCurrentPage('help'),
    onNavigateToPreference: () => setCurrentPage('preference'),
    onShowChatbot: () => {
      // #region agent log
      debugLog('App.tsx:onShowChatbot', 'opening chatbot', { showChatbot: true }, 'C');
      // #endregion
      setShowChatbot(true);
    }
  };

  const handleChatNavigation = async (action: ChatAction) => {
    switch (action.type) {
      case 'open_planning':
        if (action.origin_name) {
          setOrigin({ displayName: action.origin_name });
        }
        if (action.destination_name) {
          setDestination({ displayName: action.destination_name });
        }
        setCurrentPage('planning');
        break;
      case 'open_route_text':
        setRouteInitialViewMode('text');
        setCurrentPage('routeResult');
        break;
      case 'open_route_map':
        setRouteInitialViewMode('map');
        setCurrentPage('routeResult');
        break;
      case 'open_stations':
        setStationsSearchQuery(action.station_search_query?.trim() || '');
        setCurrentPage('stationsHome');
        break;
      case 'open_station_detail': {
        if (!action.station_id) {
          break;
        }
        const detail = await getLocationDetail(action.station_id);
        if (!detail) {
          throw new Error('station_detail_unavailable');
        }
        setSelectedStation(detail);
        setCurrentPage('stationDetail');
        break;
      }
      case 'open_help':
        setCurrentPage('help');
        break;
      case 'open_ticket_guide':
        setCurrentPage('ticketGuide');
        break;
      case 'open_concession_guide':
        setCurrentPage('concessionGuide');
        break;
      case 'open_privacy':
        setCurrentPage('privacyInfo');
        break;
      case 'open_preference':
        setCurrentPage('preference');
        break;
      case 'compute_route': {
        if (!action.origin_name || !action.destination_name) {
          break;
        }
        const originSelection = {
          displayName: action.origin_name,
          lat: action.origin_lat ?? null,
          lon: action.origin_lon ?? null,
          googlePlaceId: action.origin_google_place_id ?? null
        };
        const destinationSelection = {
          displayName: action.destination_name,
          lat: action.destination_lat ?? null,
          lon: action.destination_lon ?? null,
          googlePlaceId: action.destination_google_place_id ?? null
        };
        setOrigin(originSelection);
        setDestination(destinationSelection);
        setDepartureTime(action.departure_time || 'now');
        setCurrentRoute(null);
        setRouteLoading(true);
        setRouteError(null);
        setRouteInitialViewMode('text');
        setCurrentPage('routeResult');
        try {
          const route = await recommendRoute({
            anonymousUserId,
            origin: originSelection,
            destination: destinationSelection,
            departureTime: action.departure_time || 'now',
            preferences
          });
          setCurrentRoute(route);
        } catch {
          setRouteError('Unable to plan route. Please try again from Planning.');
          setCurrentPage('planning');
        } finally {
          setRouteLoading(false);
        }
        break;
      }
      default:
        break;
    }
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
          initialViewMode={routeInitialViewMode}
          onNavigateToPlanTime={() => setCurrentPage('planTime')}
        />
      )}
      {currentPage === 'stationsHome' && (
        <StationsHomePage
          {...navHandlers}
          initialSearchQuery={stationsSearchQuery}
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

      {showChatbot && (
        <Suspense
          fallback={
            <ChatbotLoadingShell
              onClose={() => setShowChatbot(false)}
              closeLabel={getTranslation(language, 'chatCloseLabel')}
              openingLabel={getTranslation(language, 'chatOpening')}
            />
          }
        >
          <AIChatbotSheet
            isOpen={showChatbot}
            onClose={() => setShowChatbot(false)}
            onNavigate={handleChatNavigation}
          />
        </Suspense>
      )}
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
