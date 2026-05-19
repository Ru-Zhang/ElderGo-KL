import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ai_route_sentence_service import (
    extract_route_endpoints,
    has_departure_signal,
    parse_custom_departure_iso,
    parse_departure_time,
    parse_route_sentence,
    strip_time_suffix,
)


def test_strip_time_at_1pm() -> None:
    assert strip_time_suffix("from KLCC to Monash at 1 pm") == "from KLCC to Monash"


def test_a_to_b_without_from() -> None:
    origin, dest = extract_route_endpoints("KLCC to Monash at 1 pm")
    assert origin == "KLCC"
    assert dest == "Monash"


def test_from_a_to_b_at_1130() -> None:
    parsed = parse_route_sentence("from KLCC to Monash at 11:30")
    assert parsed.origin == "KLCC"
    assert parsed.destination == "Monash"
    assert parsed.departure is not None
    assert "T11:30:00" in parsed.departure


def test_tom_1pm_tomorrow() -> None:
    iso = parse_custom_departure_iso("from KLCC to Monash at tom 1 pm")
    assert iso is not None
    assert "T13:00:00" in iso or "T01:00:00" in iso


def test_parse_departure_at_1pm_defaults_today() -> None:
    dep = parse_departure_time("at 1 pm")
    assert dep is not None
    assert "T" in dep


def test_has_departure_signal() -> None:
    assert has_departure_signal("tomorrow 6am")
    assert has_departure_signal("at 11:30")


def test_from_monash_to_klcc_tomorrow_1pm() -> None:
    parsed = parse_route_sentence("from monash to klcc at tomorrow 1pm")
    assert parsed.origin == "monash"
    assert parsed.destination == "klcc"
    assert parsed.departure is not None
    assert "T13:00:00" in parsed.departure


def test_monash_to_klcc_tom_1pm() -> None:
    parsed = parse_route_sentence("monash to klcc at tom 1 pm")
    assert parsed.origin == "monash"
    assert parsed.destination == "klcc"
    assert parsed.departure is not None
    assert "T13:00:00" in parsed.departure


def test_wanna_go_to_monash_destination_only() -> None:
    origin, dest = extract_route_endpoints("i wanna go to monash")
    assert origin is None
    assert dest == "monash"


def test_from_monash_to_kl_sentral_at_2pm_strips_time_from_destination() -> None:
    parsed = parse_route_sentence("from monash to kl sentral at 2 pm")
    assert parsed.origin == "monash"
    assert parsed.destination == "kl sentral"
    assert "at 2" not in (parsed.destination or "").lower()
    assert parsed.departure is not None
    assert "T14:00:00" in parsed.departure


def test_parse_departure_2pm_not_midday_preset() -> None:
    dep = parse_departure_time("from monash to kl sentral at 2 pm")
    assert dep is not None
    assert dep != "midday"
    assert "T14:00:00" in dep


def test_sanitize_route_endpoint_strips_trailing_time() -> None:
    from app.services.ai_route_sentence_service import sanitize_route_endpoint

    assert sanitize_route_endpoint("kl sentral at 2 pm") == "kl sentral"
