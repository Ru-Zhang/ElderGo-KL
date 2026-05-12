from pydantic import BaseModel


class AIConversationResponse(BaseModel):
    conversation_id: str


class AIMessageRequest(BaseModel):
    message: str


class AIMessageResponse(BaseModel):
    conversation_id: str
    answer: str
    in_scope: bool
