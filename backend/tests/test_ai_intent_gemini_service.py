import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ai_intent_gemini_service import is_route_recommendation_message


def test_is_route_recommendation_message() -> None:
    assert is_route_recommendation_message("I need a route recommendation")
    assert is_route_recommendation_message("can you suggest a route for me")
    assert not is_route_recommendation_message("from KLCC to Monash")
