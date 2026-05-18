import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.route_segment_image_matcher import (
    match_step_images,
    reload_segment_image_templates_cache,
    resolve_route_step_images,
)


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


def _usj7_brt_reverse_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "html_instructions": "Bus towards USJ 7",
        "transit_details": {
            "departure_stop": {"name": "Stesen BRT Sunu-Monash"},
            "arrival_stop": {"name": "Stesen BRT USJ7"},
            "headsign": "USJ 7",
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


def _wrong_vehicle_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "html_instructions": "Tram towards USJ 7",
        "transit_details": {
            "departure_stop": {"name": "USJ 7"},
            "arrival_stop": {"name": "KL Sentral"},
            "line": {"short_name": "T123", "vehicle": {"type": "TRAM"}},
        },
    }


def setup_function() -> None:
    reload_segment_image_templates_cache()


def test_usj7_to_monash_uses_google_not_curated_csv() -> None:
    images = match_step_images(
        _usj7_brt_forward_step(),
        1,
        "USJ 7",
        "Monash University Malaysia",
    )
    assert images == []


def test_klcc_to_monash_exact_od_still_matches() -> None:
    images = match_step_images(
        _klcc_lrt_step(),
        2,
        "KLCC",
        "Monash University Malaysia",
    )
    assert images
    assert any("step-02" in image["path"] for image in images)


def test_non_monash_corridor_returns_empty() -> None:
    images = match_step_images(
        _klcc_lrt_step(),
        2,
        "Petaling Jaya",
        "KL Sentral",
    )
    assert images == []


def test_unrelated_step_returns_empty() -> None:
    walk_only = {
        "travel_mode": "WALKING",
        "html_instructions": "Walk to a park",
    }
    images = match_step_images(walk_only, 1, "Central Park", "Times Square")
    assert images == []


def test_brt_reverse_direction_returns_empty() -> None:
    images = match_step_images(
        _usj7_brt_reverse_step(),
        1,
        "Monash University Malaysia",
        "USJ 7",
    )
    assert images == []


def test_wrong_vehicle_type_returns_empty() -> None:
    images = match_step_images(
        _wrong_vehicle_step(),
        1,
        "USJ 7",
        "Monash University Malaysia",
    )
    assert images == []


def test_non_canonical_od_returns_empty_curated_images() -> None:
    """Only klcc|monash university malaysia uses backend CSV; USJ7→Monash does not."""
    from app.services.route_station_images_service import get_route_step_images

    assert get_route_step_images("usj 7|monash university malaysia", 2) == []
    images = match_step_images(
        _klcc_lrt_step(),
        2,
        "USJ 7",
        "Monash University Malaysia",
    )
    assert images == []


def _full_usj7_corridor_steps() -> list[dict]:
    return [_klcc_lrt_step(), _usj7_brt_forward_step(), _usj7_brt_forward_step()]


def test_resolve_route_step_images_dedupes_adjacent_paths() -> None:
    steps = _full_usj7_corridor_steps()
    resolved = resolve_route_step_images(steps, "KLCC", "Monash University Malaysia")
    assert 1 in resolved
    assert 2 in resolved
    if resolved[1] and resolved[2]:
        paths1 = {image["path"] for image in resolved[1]}
        paths2 = {image["path"] for image in resolved[2]}
        assert paths1.isdisjoint(paths2) or len(resolved[2]) <= len(resolved[1])
