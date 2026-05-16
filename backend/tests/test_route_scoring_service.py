import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.preferences import TravelPreferences
from app.services.google_maps_service import CandidateRoute
from app.services.route_scoring_service import choose_best_with_summary


def _transit_step(line: str = "KJ", accessible: bool = False) -> dict:
    transit_details = {"line": {"short_name": line}}
    if accessible:
        transit_details["wheelchair_accessible"] = True
    return {"travel_mode": "TRANSIT", "transit_details": transit_details}


def _walking_step(unknown_access: bool = False, not_supported_access: bool = False) -> dict:
    step = {
        "travel_mode": "WALKING",
        "start_location": {"lat": 3.1, "lng": 101.6},
        "end_location": {"lat": 3.2, "lng": 101.7},
    }
    if unknown_access:
        step["accessibility_test"] = "unknown"
    if not_supported_access:
        step["accessibility_test"] = "not_supported"
    return step


def _candidate(
    duration: int,
    walking: int,
    transfers: int,
    *,
    accessible_transit: bool = False,
    transit: bool = True,
) -> CandidateRoute:
    steps = [_walking_step()]
    if transit:
        steps.append(_transit_step(accessible=accessible_transit))
    return CandidateRoute(
        duration_minutes=duration,
        walking_distance_meters=walking,
        transfers=transfers,
        steps=steps,
        polyline=None,
        raw={},
    )


def test_no_preferences_selects_fastest_google_candidate() -> None:
    candidates = [
        _candidate(30, 100, 0),
        _candidate(20, 900, 2),
    ]
    result = choose_best_with_summary(candidates, TravelPreferences())
    assert result is not None
    assert result.candidate.duration_minutes == 20
    assert result.preference_summary_key == "routePreferenceFastest"
    assert result.ranking_primary_factor == "duration"


def test_single_least_walk_preference_uses_duration_tie_break() -> None:
    candidates = [
        _candidate(20, 300, 1),
        _candidate(25, 100, 2),
        _candidate(15, 100, 3),
    ]
    prefs = TravelPreferences(least_walk=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.duration_minutes == 15
    assert result.candidate.walking_distance_meters == 100
    assert result.ranking_primary_factor == "walk"


def test_single_fewest_transfers_preference_uses_duration_tie_break() -> None:
    candidates = [
        _candidate(20, 100, 2),
        _candidate(30, 400, 0),
        _candidate(25, 500, 0),
    ]
    prefs = TravelPreferences(fewest_transfers=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.duration_minutes == 25
    assert result.candidate.transfers == 0
    assert result.ranking_primary_factor == "transfers"


def test_single_accessibility_preference_uses_duration_tie_break() -> None:
    candidates = [
        _candidate(20, 100, 1),
        _candidate(30, 500, 2, accessible_transit=True),
        _candidate(25, 600, 3, accessible_transit=True),
    ]
    prefs = TravelPreferences(accessibility_first=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.duration_minutes == 25
    assert result.ranking_primary_factor == "accessibility"


def test_multiple_preferences_follow_user_priority_order() -> None:
    low_walk = _candidate(40, 100, 2)
    accessible = _candidate(45, 500, 2, accessible_transit=True)
    prefs = TravelPreferences(
        accessibility_first=True,
        least_walk=True,
        priority_order=["walk", "accessibility", "transfers"],
    )
    result = choose_best_with_summary([accessible, low_walk], prefs)
    assert result is not None
    assert result.candidate is low_walk
    assert result.ranking_primary_factor == "walk"
    assert result.ranking_secondary_factor == "accessibility"


def test_priority_order_uses_fastest_duration_as_tie_break() -> None:
    slower_low_walk = _candidate(30, 100, 2)
    faster_low_walk = _candidate(20, 100, 3)
    prefs = TravelPreferences(
        least_walk=True,
        priority_order=["walk", "accessibility", "transfers"],
    )
    result = choose_best_with_summary([slower_low_walk, faster_low_walk], prefs)
    assert result is not None
    assert result.candidate is faster_low_walk
    assert result.ranking_primary_factor == "walk"
    assert result.ranking_secondary_factor == "duration"


def test_ranking_returns_only_a_google_candidate_from_the_input_pool() -> None:
    google_fast = _candidate(20, 600, 2)
    google_preferred = _candidate(25, 100, 2)
    prefs = TravelPreferences(least_walk=True)
    result = choose_best_with_summary([google_fast, google_preferred], prefs)
    assert result is not None
    assert result.candidate in [google_fast, google_preferred]
    assert result.candidate is google_preferred


def test_all_preferences_follow_full_user_order() -> None:
    fewer_transfers = _candidate(50, 600, 0)
    less_walk = _candidate(45, 100, 2)
    accessible = _candidate(40, 500, 1)
    prefs = TravelPreferences(
        accessibility_first=True,
        least_walk=True,
        fewest_transfers=True,
        priority_order=["transfers", "walk", "accessibility"],
    )
    result = choose_best_with_summary([accessible, less_walk, fewer_transfers], prefs)
    assert result is not None
    assert result.candidate is fewer_transfers
    assert result.ranking_primary_factor == "transfers"
    assert result.ranking_secondary_factor == "walk"


def test_missing_invalid_partial_priority_order_normalizes_to_default() -> None:
    prefs = TravelPreferences.model_validate(
        {
            "accessibility_first": True,
            "least_walk": True,
            "fewest_transfers": True,
            "priority_order": ["walk", "bad"],
        }
    )
    assert prefs.priority_order == ["walk", "accessibility", "transfers"]


def test_walk_only_candidates_are_ignored() -> None:
    walk_only = _candidate(5, 100, 0, transit=False)
    transit = _candidate(20, 300, 1)
    result = choose_best_with_summary([walk_only, transit], TravelPreferences())
    assert result is not None
    assert result.candidate is transit
