import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.curated_corridor_policy import (
    CANONICAL_CORRIDOR_ROUTE_KEY,
    csv_step_for_google_step,
    detect_curated_profile,
    google_steps_use_usj7_kjl_brt,
    is_canonical_klcc_to_monash_od,
    should_use_curated_route_csv,
)


def _usj7_corridor_steps() -> list[dict]:
    return [
        {"travel_mode": "WALKING", "html_instructions": "Walk to KLCC"},
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {"name": "KLCC"},
                "arrival_stop": {"name": "USJ 7"},
                "line": {"short_name": "KJ", "vehicle": {"type": "SUBWAY"}},
            },
        },
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {"name": "Stesen BRT USJ 7"},
                "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
            },
        },
    ]


def _ss18_shortcut_steps() -> list[dict]:
    return [
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {"name": "Stesen BRT SS18"},
                "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
            },
        },
    ]


def test_klcc_lrt_to_monash_is_canonical() -> None:
    assert is_canonical_klcc_to_monash_od("KLCC LRT", "Monash University Malaysia")
    assert should_use_curated_route_csv("KLCC", "Monash University", google_steps=_usj7_corridor_steps())


def test_usj7_origin_profile_without_klcc() -> None:
    steps = [
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {"name": "Stesen BRT USJ 7"},
                "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
            },
        },
        {"travel_mode": "WALKING", "html_instructions": "Walk to Monash University Malaysia"},
    ]
    assert detect_curated_profile("USJ 7", "Monash University", google_steps=steps) == "usj7_brt"


def test_kl_sentral_to_monash_is_not_canonical() -> None:
    assert not is_canonical_klcc_to_monash_od("KL Sentral", "Monash University Malaysia")


def test_ss18_route_does_not_use_curated_csv() -> None:
    assert not should_use_curated_route_csv(
        "KLCC",
        "Monash University Malaysia",
        google_steps=_ss18_shortcut_steps(),
    )


def test_usj7_corridor_steps_detected() -> None:
    assert google_steps_use_usj7_kjl_brt(_usj7_corridor_steps())


def test_canonical_route_key_constant() -> None:
    assert CANONICAL_CORRIDOR_ROUTE_KEY == "klcc|monash university malaysia"
