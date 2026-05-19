import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ai_guardrail_service import is_travel_related
from app.services.ai_quick_question_service import (
    GUIDE_QUICK_IDS,
    match_quick_question,
    resolve_quick_guide_answer,
)


def test_match_ticket_quick_question_exact() -> None:
    m = match_quick_question("How do I buy train tickets?")
    assert m is not None
    assert m.question_id == "ticket_guide"
    assert m.match_kind == "exact"


def test_match_flow_weather_chip() -> None:
    m = match_quick_question("Check the weather")
    assert m is not None
    assert m.question_id == "weather"


def test_guide_quick_resolves_blocks() -> None:
    answer, blocks, actions = resolve_quick_guide_answer("privacy", "en")
    assert "privacy" in answer.lower() or "Privacy" in answer
    assert blocks
    assert actions[0].type == "open_privacy"


def test_monash_to_klcc_travel_related() -> None:
    assert is_travel_related("monash to klcc at 1pm") is True


def test_guide_ids_exclude_flow() -> None:
    assert "plan_route" not in GUIDE_QUICK_IDS
