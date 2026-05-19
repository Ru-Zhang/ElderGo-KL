import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.curated_corridor_policy import (
    csv_step_for_google_step,
    detect_curated_profile,
)
from app.services.route_segment_image_matcher import resolve_route_step_images


def _usj7_brt_forward_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "html_instructions": "Bus towards Monash University",
        "transit_details": {
            "departure_stop": {"name": "Stesen BRT USJ7"},
            "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
            "headsign": "Sunway-Setia Jaya",
            "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}},
        },
    }


def _klcc_lrt_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "html_instructions": "Train towards USJ 7",
        "transit_details": {
            "departure_stop": {"name": "KLCC"},
            "arrival_stop": {"name": "USJ 7"},
            "headsign": "Putra Heights",
            "line": {"short_name": "KJ", "name": "LRT Kelana Jaya Line", "vehicle": {"type": "SUBWAY"}},
        },
    }


def _walk_to_monash_step() -> dict:
    return {
        "travel_mode": "WALKING",
        "html_instructions": "Walk to Monash University Malaysia",
    }


def test_full_corridor_maps_steps_one_to_five() -> None:
    steps = [
        {"travel_mode": "WALKING", "html_instructions": "Walk to KLCC"},
        _klcc_lrt_step(),
        {
            "travel_mode": "WALKING",
            "html_instructions": "Walk to USJ 7",
        },
        _usj7_brt_forward_step(),
        _walk_to_monash_step(),
    ]
    resolved = resolve_route_step_images(steps, "KLCC", "Monash University Malaysia")
    assert detect_curated_profile("KLCC", "Monash University Malaysia", google_steps=steps) == "full"
    assert any("step-01" in image["path"] for image in resolved[1])
    assert any("step-02" in image["path"] for image in resolved[2])
    assert any("step-03" in image["path"] for image in resolved[3])
    assert any("step-04" in image["path"] for image in resolved[4])
    assert any("step-05" in image["path"] for image in resolved[5])


def test_usj7_brt_to_monash_uses_steps_three_four_five() -> None:
    steps = [
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {"name": "USJ 7"},
                "arrival_stop": {"name": "USJ 7"},
                "line": {"short_name": "KJ", "vehicle": {"type": "SUBWAY"}},
            },
        },
        _usj7_brt_forward_step(),
        _walk_to_monash_step(),
    ]
    profile = detect_curated_profile("USJ 7", "Monash University Malaysia", google_steps=steps)
    assert profile == "usj7_brt"
    resolved = resolve_route_step_images(steps, "USJ 7", "Monash University Malaysia")
    assert any("step-03" in image["path"] for image in resolved[1])
    assert any("step-04" in image["path"] for image in resolved[2])
    assert any("step-05" in image["path"] for image in resolved[3])


def test_sunu_monash_to_monash_uses_step_five_only() -> None:
    steps = [_walk_to_monash_step()]
    profile = detect_curated_profile(
        "Stesen BRT Sunu-Monash",
        "Monash University Malaysia",
        google_steps=steps,
    )
    assert profile == "sunu_arrival"
    assert csv_step_for_google_step(
        _walk_to_monash_step(),
        "sunu_arrival",
        origin_name="Stesen BRT Sunu-Monash",
        destination_name="Monash University Malaysia",
    ) == 5
    resolved = resolve_route_step_images(
        steps,
        "Stesen BRT Sunu-Monash",
        "Monash University Malaysia",
    )
    assert len(resolved) == 1
    assert any("step-05" in image["path"] for image in resolved[1])


def test_usj7_brt_only_two_legs_maps_four_and_five() -> None:
    steps = [_usj7_brt_forward_step(), _walk_to_monash_step()]
    resolved = resolve_route_step_images(steps, "USJ 7", "Monash University Malaysia")
    assert any("step-04" in image["path"] for image in resolved[1])
    assert any("step-05" in image["path"] for image in resolved[2])


def _ss18_brt_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "transit_details": {
            "departure_stop": {"name": "Stesen BRT SS18"},
            "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
            "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
        },
    }


def test_kl_sentral_monash_via_usj7_uses_steps_three_four_five() -> None:
    steps = [
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {"name": "KL Sentral"},
                "arrival_stop": {"name": "USJ 7"},
                "line": {"short_name": "KJ", "vehicle": {"type": "SUBWAY"}},
            },
        },
        _usj7_brt_forward_step(),
        _walk_to_monash_step(),
    ]
    profile = detect_curated_profile(
        "KL Sentral",
        "Monash University Malaysia",
        google_steps=steps,
    )
    assert profile == "usj7_brt"
    resolved = resolve_route_step_images(steps, "KL Sentral", "Monash University Malaysia")
    assert any("step-03" in image["path"] for image in resolved[1])
    assert any("step-04" in image["path"] for image in resolved[2])
    assert any("step-05" in image["path"] for image in resolved[3])
    assert not any("step-01" in image["path"] for paths in resolved.values() for image in paths)


def test_kl_sentral_monash_ss18_no_curated() -> None:
    steps = [_ss18_brt_step(), _walk_to_monash_step()]
    assert (
        detect_curated_profile("KL Sentral", "Monash University Malaysia", google_steps=steps)
        is None
    )
    assert resolve_route_step_images(steps, "KL Sentral", "Monash University Malaysia") == {}
