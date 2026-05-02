from typing import Optional

from pydantic import BaseModel


class AIConversationResponse(BaseModel):
    conversation_id: str


class AIMessageRequest(BaseModel):
    message: str
    # Optional context ids are placeholders for future grounded responses.
    current_route_id: Optional[str] = None
    selected_location_id: Optional[str] = None


class AIMessageResponse(BaseModel):
    conversation_id: str
    answer: str
    in_scope: bool
