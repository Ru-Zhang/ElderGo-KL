import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.ai import AIMessageRequest
from app.services.ai_guardrail_service import is_travel_related
from app.services.ai_intent_service import classify_intent
from app.services.ai_topic_inference_service import infer_probable_guide_intent


def test_discount_maps_to_concession_guide() -> None:
    message = "i wanna know the discount"
    assert infer_probable_guide_intent(message) == "concession_guide"
    assert is_travel_related(message)
    assert classify_intent(message, AIMessageRequest(message=message)) == "concession_guide"


def test_ticket_phrase_maps_to_ticket_guide() -> None:
    message = "how do I buy a ticket"
    assert infer_probable_guide_intent(message) == "ticket_guide"
    assert classify_intent(message, AIMessageRequest(message=message)) == "ticket_guide"
