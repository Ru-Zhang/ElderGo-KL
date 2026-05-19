import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.routes import PlaceInput
from app.services.ai_flow_service import _parse_custom_departure_iso, _parse_departure_time
from app.services.departure_time_service import format_departure_display_label
from app.services.google_maps_service import _place_value


def test_place_value_prefers_coordinates_over_internal_place_id() -> None:
    place = PlaceInput(
        display_name="KLCC",
        lat=3.157,
        lon=101.712,
        google_place_id="eldergo:place:klcc",
    )
    assert _place_value(place) == "3.157,101.712"


def test_parse_tomorrow_morning_departure() -> None:
    iso = _parse_custom_departure_iso("tomorrow 6am")
    assert iso is not None
    assert "T06:00:00" in iso or "T06:00:00+08:00" in iso
    assert _parse_departure_time("tomorrow 6am") == iso


def test_departure_display_label_for_preset() -> None:
    label = format_departure_display_label("morning_peak", "en")
    assert "Morning peak" in label


def test_parse_at_1pm_iso() -> None:
    iso = _parse_custom_departure_iso("at 1 pm")
    assert iso is not None


def test_preference_hint_extraction() -> None:
    from app.services.ai_route_sentence_service import extract_preference_hint

    assert extract_preference_hint("least walk please") == "least_walk"
    assert extract_preference_hint("无障碍优先") == "accessibility_first"


def test_klcc_to_monash_sentence_parse() -> None:
    from app.services.ai_route_sentence_service import parse_route_sentence

    parsed = parse_route_sentence("KLCC to Monash at 1 pm")
    assert parsed.origin == "KLCC"
    assert parsed.destination == "Monash"
    assert parsed.departure is not None


def test_suggest_place_alias_typo() -> None:
    from app.services.ai_route_parse_service import suggest_place_alias

    assert suggest_place_alias("monash uni") == "Monash University Malaysia"
    assert suggest_place_alias("klcc") == "Kuala Lumpur City Centre"


def test_confirm_yes_no() -> None:
    from app.services.ai_route_sentence_service import is_confirm_no, is_confirm_yes

    assert is_confirm_yes("yes")
    assert is_confirm_yes("是")
    assert is_confirm_no("no")
    assert is_confirm_no("设置偏好")
