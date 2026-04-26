from pydantic import BaseModel


class AIConversationResponse(BaseModel):
    conversation_id: str


class AIMessageRequest(BaseModel):
    message: str
    current_route_id: str | None = None
    selected_location_id: str | None = None


class AIMessageResponse(BaseModel):
    conversation_id: str
    answer: str
    in_scope: bool
