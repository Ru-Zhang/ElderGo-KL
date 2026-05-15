"""Map UI language to template language codes used by chatbot services."""

from app.schemas.ai import AIMessageRequest
from app.services.ai_intent_service import detect_language


def resolve_response_language(request: AIMessageRequest, message: str) -> str:
    """Prefer app UI language (EN/BM) so answers match the user's selected language."""
    if request.ui_language == "BM":
        return "ms"
    if request.ui_language == "EN":
        return "en"
    return detect_language(message)
