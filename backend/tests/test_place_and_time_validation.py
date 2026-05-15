import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ai_flow_service import _departure_input_is_invalid, _parse_departure_time
from app.services.ai_route_parse_service import (
    classify_place_input,
    is_unclear_place_reply,
    refine_place_query_for_slot,
)


def test_classify_place_input_cases() -> None:
    assert classify_place_input("klcc") == "ok"
    assert classify_place_input("d") == "too_short"
    assert classify_place_input("") == "empty"
    assert classify_place_input("???") in {"too_short", "implausible"}
    assert classify_place_input("from monash university malaysia to kuala lumpur airport 1") == "route_sentence"
    long_gibberish = "x" * 80
    assert classify_place_input(long_gibberish) == "too_long"


def test_full_route_sentence_not_unclear() -> None:
    message = (
        "i want to go from monash university malaysia to kuala lumpur airport 1 "
        "at the evening, could you please recommend a route for me?"
    )
    assert not is_unclear_place_reply(message)


def test_refine_place_query_for_destination_slot() -> None:
    message = "from monash university malaysia to klcc please"
    assert refine_place_query_for_slot(message, "destination") == "klcc"


def test_known_place_skips_api_lookup() -> None:
    from app.services.ai_route_parse_service import lookup_known_kv_place

    known = lookup_known_kv_place("monash university malaysia")
    assert known is not None
    assert known["lat"] == 3.0636


def test_message_has_plan_route_endpoints() -> None:
    from app.services.ai_route_parse_service import message_has_plan_route_endpoints

    assert message_has_plan_route_endpoints("from Monash University to KL Sentral")
    assert not message_has_plan_route_endpoints("cafes near KLCC")


def test_departure_time_parsing() -> None:
    assert _parse_departure_time("evening") == "evening"
    assert _parse_departure_time("at the evening") == "evening"
    assert _parse_departure_time("3pm") == "afternoon"
    assert _parse_departure_time("9am") == "morning"
    assert _parse_departure_time("下午") == "afternoon"
    assert _parse_departure_time("2") == "morning"
    assert _parse_departure_time("5") is None
    assert _departure_input_is_invalid("5")
    assert not _departure_input_is_invalid("hello")
