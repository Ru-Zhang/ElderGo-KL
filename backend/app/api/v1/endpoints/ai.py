from uuid import uuid4

from fastapi import APIRouter

from app.schemas.ai import AIConversationResponse, AIMessageRequest, AIMessageResponse
from app.services.ai_guardrail_service import is_in_scope

router = APIRouter()


@router.post("/conversations", response_model=AIConversationResponse)
def create_conversation() -> AIConversationResponse:
    return AIConversationResponse(conversation_id=f"conv_{uuid4().hex[:16]}")


@router.post("/conversations/{conversation_id}/messages", response_model=AIMessageResponse)
def send_message(conversation_id: str, payload: AIMessageRequest) -> AIMessageResponse:
    if not is_in_scope(payload.message):
        return AIMessageResponse(
            conversation_id=conversation_id,
            in_scope=False,
            answer=(
                "I can help with ElderGo KL routes, stations, accessibility, tickets, "
                "concession information, privacy, and app usage only."
            ),
        )
    return AIMessageResponse(
        conversation_id=conversation_id,
        in_scope=True,
        answer=(
            "I can help with this ElderGo KL topic. Some live data is not connected yet, "
            "so I will say unknown whenever station, route, or accessibility details are not verified."
        ),
    )
