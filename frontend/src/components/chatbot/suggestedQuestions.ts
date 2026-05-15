import { TranslationKey } from '../../i18n/translations';
import { ChatAction } from '../../types/ai';

export interface SuggestedQuestion {
  id: string;
  labelKey: TranslationKey;
  messageKey: TranslationKey;
}

export const SUGGESTED_QUESTIONS: SuggestedQuestion[] = [
  { id: 'plan', labelKey: 'chatSuggest_planRoute', messageKey: 'chatSuggest_planRouteMsg' },
  { id: 'stations', labelKey: 'chatSuggest_stations', messageKey: 'chatSuggest_stationsMsg' },
  { id: 'weather', labelKey: 'chatSuggest_weather', messageKey: 'chatSuggest_weatherMsg' },
  { id: 'tickets', labelKey: 'chatSuggest_tickets', messageKey: 'chatSuggest_ticketsMsg' },
  { id: 'concession', labelKey: 'chatSuggest_concession', messageKey: 'chatSuggest_concessionMsg' },
  { id: 'privacy', labelKey: 'chatSuggest_privacy', messageKey: 'chatSuggest_privacyMsg' },
  { id: 'preferences', labelKey: 'chatSuggest_preferences', messageKey: 'chatSuggest_preferencesMsg' }
];

export function formatChatActionLabel(
  action: ChatAction,
  t: (key: TranslationKey) => string
): string {
  if (action.type === 'open_station_detail' && action.station_name?.trim()) {
    return `${t('chatAction_viewStationPage')}: ${action.station_name.trim()}`;
  }
  if (action.type === 'open_planning' && action.origin_name && action.destination_name) {
    return `${t('chatAction_openPlanningPrefill')}: ${action.origin_name} → ${action.destination_name}`;
  }
  if (action.type === 'compute_route' && action.origin_name && action.destination_name) {
    return `${t('chatAction_computeRoute')}: ${action.origin_name} → ${action.destination_name}`;
  }
  const labelKey = getChatActionLabelKey(action);
  return labelKey ? t(labelKey) : action.type;
}

export function getChatActionLabelKey(action: {
  type: string;
  origin_name?: string | null;
  destination_name?: string | null;
}): TranslationKey | null {
  if (action.type === 'compute_route') {
    return 'chatAction_computeRoute';
  }
  if (action.type === 'open_planning' && action.origin_name && action.destination_name) {
    return 'chatAction_openPlanningPrefill';
  }
  return CHAT_ACTION_LABEL_KEYS[action.type] ?? null;
}

export const CHAT_ACTION_LABEL_KEYS: Record<string, TranslationKey> = {
  open_planning: 'chatAction_openPlanning',
  open_route_text: 'chatAction_openRouteText',
  open_route_map: 'chatAction_openRouteMap',
  open_stations: 'chatAction_openStations',
  open_station_detail: 'chatAction_openStationDetail',
  open_help: 'chatAction_openHelp',
  open_ticket_guide: 'chatAction_openTicketGuide',
  open_concession_guide: 'chatAction_openConcessionGuide',
  open_privacy: 'chatAction_openPrivacy',
  open_preference: 'chatAction_openPreference',
  compute_route: 'chatAction_computeRoute'
};
