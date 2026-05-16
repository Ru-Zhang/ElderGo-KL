import { lazy, Suspense, useEffect, useLayoutEffect, useRef, useState } from 'react';
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
import { getLocationDetail } from '../services/locationsApi';
import { ChatAction } from '../types/ai';
import { buildRouteCacheKey } from '../utils/routeCacheKey';
import { getCachedRoute, recommendRoute } from '../services/routesApi';
import { ApiError } from '../services/api';
import { placeSelectionFromChatAction } from '../utils/placeSelection';
import { resolveRouteErrorMessage } from '../utils/routeErrors';
import { resetPageScroll } from '../utils/resetPageScroll';
import type { PlaceSelection } from '../types/locations';

const AIChatbotSheet = lazy(() => import('../components/chatbot/AIChatbotSheet'));

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
    origin,
    destination,
    preferences,
    setSelectedStation,
    setOrigin,
    setDestination,
    setDepartureTime,
    setCurrentRoute,
    setRouteLoading,
    setRouteError,
    setRouteErrorCode,
  } = useAppContext();
  const [stationsSearchQuery, setStationsSearchQuery] = useState('');
  const routeAbortRef = useRef<AbortController | null>(null);
  const routeRequestIdRef = useRef(0);
  const preferencesRef = useRef(preferences);
  preferencesRef.current = preferences;

  const requestRecommendedRoute = async (
    routeOrigin: PlaceSelection,
    routeDestination: PlaceSelection,
    apiDepartureTime: string,
    logSource: string,
  ) => {
    setDepartureTime(apiDepartureTime);
    routeAbortRef.current?.abort();
    const controller = new AbortController();
    routeAbortRef.current = controller;
    const requestId = ++routeRequestIdRef.current;
    setRouteError(null);
    setRouteErrorCode(null);

    const activePreferences = preferencesRef.current;
    const routeRequest = {
      anonymousUserId,
      origin: routeOrigin,
      destination: routeDestination,
      departureTime: apiDepartureTime,
      preferences: activePreferences,
    };

    const cachedRoute = getCachedRoute(routeRequest);
    if (cachedRoute) {
      setCurrentRoute(cachedRoute);
      setRouteLoading(false);
      setRouteInitialViewMode('text');
      setCurrentPage('routeResult');
      return;
    }

    setRouteLoading(true);
    setCurrentRoute(null);
    setRouteInitialViewMode('text');
    setCurrentPage('routeResult');

    try {
      const route = await recommendRoute(routeRequest, controller.signal);
      if (requestId !== routeRequestIdRef.current) return;
      if (controller.signal.aborted) return;
      setCurrentRoute(route);
    } catch (error) {
      if (requestId !== routeRequestIdRef.current) return;
      if (controller.signal.aborted) {
        return;
      }
      const t = (key: Parameters<typeof getTranslation>[1]) => getTranslation(language, key);
      setRouteErrorCode(error instanceof ApiError ? error.code ?? null : null);
      setRouteError(resolveRouteErrorMessage(error, t, 'planTimeUnableToRoute'));
    } finally {
      if (requestId === routeRequestIdRef.current) {
        setRouteLoading(false);
      }
    }
  };

  const handleShowRouteFromPlan = async (apiDepartureTime: string) => {
    if (!origin || !destination) return;
    await requestRecommendedRoute(origin, destination, apiDepartureTime, 'App.tsx:handleShowRouteFromPlan');
  };

  useEffect(() => {
    void import('../components/chatbot/AIChatbotSheet');
  }, []);

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

  // Shared navigation callbacks keep page switching wiring centralized.
  const navHandlers = {
    onNavigateToPlanning: () => setCurrentPage('planning'),
    onNavigateToStation: () => setCurrentPage('stationsHome'),
    onNavigateToHelp: () => setCurrentPage('help'),
    onNavigateToPreference: () => setCurrentPage('preference'),
    onShowChatbot: () => {
      setShowChatbot(true);
    }
  };

  const handleChatNavigation = async (action: ChatAction) => {
    switch (action.type) {
      case 'open_planning':
        if (action.origin_name) {
          setOrigin({
            displayName: action.origin_name,
            lat: action.origin_lat ?? null,
            lon: action.origin_lon ?? null,
            googlePlaceId: action.origin_google_place_id ?? null,
          });
        }
        if (action.destination_name) {
          setDestination({
            displayName: action.destination_name,
            lat: action.destination_lat ?? null,
            lon: action.destination_lon ?? null,
            googlePlaceId: action.destination_google_place_id ?? null,
          });
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
        const originSelection = placeSelectionFromChatAction({
          displayName: action.origin_name,
          lat: action.origin_lat,
          lon: action.origin_lon,
          googlePlaceId: action.origin_google_place_id,
        });
        const destinationSelection = placeSelectionFromChatAction({
          displayName: action.destination_name,
          lat: action.destination_lat,
          lon: action.destination_lon,
          googlePlaceId: action.destination_google_place_id,
        });
        setOrigin(originSelection);
        setDestination(destinationSelection);
        await requestRecommendedRoute(
          originSelection,
          destinationSelection,
          action.departure_time || 'now',
          'App.tsx:compute_route',
        );
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
          onRequestRoute={(apiDepartureTime) => void handleShowRouteFromPlan(apiDepartureTime)}
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
