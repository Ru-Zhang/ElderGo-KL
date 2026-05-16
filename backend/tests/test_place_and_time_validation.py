from app.services.ai_flow_service import _departure_input_is_invalid, _parse_departure_time


def test_departure_time_parsing() -> None:
    assert _parse_departure_time("evening") == "night"
    assert _parse_departure_time("morning rush") == "morning_peak"
    assert _parse_departure_time("3pm") == "midday"
    assert _parse_departure_time("9am") == "morning_peak"
    assert _parse_departure_time("6pm") == "evening_peak"
    assert _parse_departure_time("10pm") == "night"
    assert _parse_departure_time("2") == "midday"
    assert _parse_departure_time("6") is None


def test_departure_input_invalid() -> None:
    assert _departure_input_is_invalid("maybe later") is True
    assert _departure_input_is_invalid("morning_peak") is False
