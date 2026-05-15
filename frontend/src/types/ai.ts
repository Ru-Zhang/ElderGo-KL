export type ChatFlowType = 'station_info' | 'weather' | 'plan_route' | null;

export type ChatActionType =
  | 'open_planning'
  | 'open_route_text'
  | 'open_route_map'
  | 'open_stations'
  | 'open_station_detail'
  | 'open_help'
  | 'open_ticket_guide'
  | 'open_concession_guide'
  | 'open_privacy'
  | 'open_preference'
  | 'compute_route';

export type ChatBlockType =
  | 'heading'
  | 'paragraph'
  | 'bullets'
  | 'numbered'
  | 'key_values'
  | 'callout'
  | 'sources'
  | 'hours'
  | 'place_cards';

export type ResponseSourceType = 'flow' | 'db' | 'api' | 'gemini' | 'gemini_maps';

export type CalloutTone = 'info' | 'warning' | 'success';
export type KeyValueEmphasis =
  | 'supported'
  | 'not_supported'
  | 'unknown'
  | 'neutral'
  | 'highlight'
  | 'route_endpoint';

export interface KeyValueRow {
  label: string;
  value: string;
  emphasis?: KeyValueEmphasis | null;
}

export interface SourceLink {
  title: string;
  url: string;
  org?: string | null;
}

export interface ChatBlock {
  type: ChatBlockType;
  text?: string | null;
  items?: string[] | null;
  rows?: KeyValueRow[] | null;
  tone?: CalloutTone | null;
  links?: SourceLink[] | null;
}

export interface ChatAction {
  type: ChatActionType;
  station_id?: string | null;
  station_name?: string | null;
  origin_name?: string | null;
  destination_name?: string | null;
  station_search_query?: string | null;
  departure_time?: string | null;
  origin_lat?: number | null;
  origin_lon?: number | null;
  origin_google_place_id?: string | null;
  destination_lat?: number | null;
  destination_lon?: number | null;
  destination_google_place_id?: string | null;
}

export interface AIConversationResponse {
  conversation_id: string;
}

export interface AIMessageContext {
  has_current_route?: boolean;
  origin_name?: string | null;
  destination_name?: string | null;
  selected_station_id?: string | null;
  selected_station_name?: string | null;
  chat_flow?: ChatFlowType;
  flow_slots?: Record<string, string>;
}

export interface AIMessageResponse {
  conversation_id: string;
  answer: string;
  answer_blocks: ChatBlock[];
  in_scope: boolean;
  actions: ChatAction[];
  chat_flow?: ChatFlowType;
  flow_slots?: Record<string, string>;
  response_source?: ResponseSourceType | null;
}
