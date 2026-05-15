from typing import Literal

from pydantic import BaseModel, Field


ChatFlowType = Literal["station_info", "weather", "plan_route"] | None

ChatActionType = Literal[
    "open_planning",
    "open_route_text",
    "open_route_map",
    "open_stations",
    "open_station_detail",
    "open_help",
    "open_ticket_guide",
    "open_concession_guide",
    "open_privacy",
    "open_preference",
    "compute_route",
]

ChatBlockType = Literal[
    "heading",
    "paragraph",
    "bullets",
    "numbered",
    "key_values",
    "callout",
    "sources",
    "hours",
    "place_cards",
]

ResponseSourceType = Literal["flow", "db", "api", "gemini", "gemini_maps"]

CalloutTone = Literal["info", "warning", "success"]
KeyValueEmphasis = Literal["supported", "not_supported", "unknown", "neutral", "highlight", "route_endpoint"]


class KeyValueRow(BaseModel):
    label: str
    value: str
    emphasis: KeyValueEmphasis | None = None


class SourceLink(BaseModel):
    title: str
    url: str
    org: str | None = None


class ChatBlock(BaseModel):
    type: ChatBlockType
    text: str | None = None
    items: list[str] | None = None
    rows: list[KeyValueRow] | None = None
    tone: CalloutTone | None = None
    links: list[SourceLink] | None = None


class ChatAction(BaseModel):
    type: ChatActionType
    station_id: str | None = None
    station_name: str | None = None
    origin_name: str | None = None
    destination_name: str | None = None
    station_search_query: str | None = None
    departure_time: str | None = None
    origin_lat: float | None = None
    origin_lon: float | None = None
    origin_google_place_id: str | None = None
    destination_lat: float | None = None
    destination_lon: float | None = None
    destination_google_place_id: str | None = None


class AIConversationResponse(BaseModel):
    conversation_id: str


UiLanguageCode = Literal["EN", "BM"]


class AIMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    ui_language: UiLanguageCode = "EN"
    has_current_route: bool = False
    origin_name: str | None = None
    destination_name: str | None = None
    selected_station_id: str | None = None
    selected_station_name: str | None = None
    chat_flow: ChatFlowType = None
    flow_slots: dict[str, str] = Field(default_factory=dict)


class AIMessageResponse(BaseModel):
    conversation_id: str
    answer: str
    answer_blocks: list[ChatBlock] = Field(default_factory=list)
    in_scope: bool
    actions: list[ChatAction] = Field(default_factory=list)
    chat_flow: ChatFlowType = None
    flow_slots: dict[str, str] = Field(default_factory=dict)
    response_source: ResponseSourceType | None = None
