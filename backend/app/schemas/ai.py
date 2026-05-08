from typing import Optional

from pydantic import BaseModel, Field


class AIConversationResponse(BaseModel):
    conversation_id: str


class AIMessageRequest(BaseModel):
    message: str
    # Optional context ids enable retrieval-grounded AI responses.
    current_route_id: Optional[str] = None
    selected_location_id: Optional[str] = None
    anonymous_user_id: Optional[str] = None


class AIMessageResponse(BaseModel):
    conversation_id: str
    answer: str
    in_scope: bool
    response_source: str = "fallback"
    grounded: bool = False
    used_data_keys: list[str] = Field(default_factory=list)
