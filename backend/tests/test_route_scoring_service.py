import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.preferences import TravelPreferences
from app.services.google_maps_service import CandidateRoute
from app.services.route_scoring_service import choose_best_with_summary


def _transit_step() -> dict:
    return {"travel_mode": "TRANSIT", "transit_details": {}}


def _walking_step() -> dict:
    return {
        "travel_mode": "WALKING",
        "start_location": {"lat": 3.1, "lng": 101.6},
        "end_location": {"lat": 3.2, "lng": 101.7},
    }


def _candidate(duration: int, walking: int, transfers: int, steps: list | None = None) -> CandidateRoute:
    default_steps = [_walking_step(), _transit_step(), _walking_step()]
    return CandidateRoute(
        duration_minutes=duration,
        walking_distance_meters=walking,
        transfers=transfers,
        steps=steps if steps is not None else default_steps,
        polyline=None,
        raw={},
    )


def test_choose_best_prefers_fewer_transfers_when_enabled() -> None:
    candidates = [
        _candidate(30, 200, 2),
        _candidate(32, 250, 0),
    ]
    prefs = TravelPreferences(fewest_transfers=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.transfers == 0


def test_choose_best_always_returns_one_when_candidates_exist() -> None:
    candidates = [_candidate(40, 900, 3)]
    prefs = TravelPreferences(accessibility_first=True, least_walk=True, fewest_transfers=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.duration_minutes == 40


def test_preference_summary_key_for_accessibility() -> None:
    walking_step = {
        "travel_mode": "WALKING",
        "start_location": {"lat": 3.1, "lng": 101.6},
        "end_location": {"lat": 3.2, "lng": 101.7},
    }
    transit_step = {
        "travel_mode": "TRANSIT",
        "transit_details": {"line": {"short_name": "KJ"}},
    }
    candidates = [_candidate(25, 300, 1, steps=[walking_step, transit_step])]
    prefs = TravelPreferences(accessibility_first=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.preference_summary_key == "routePreferenceAccessibility"


def test_walk_only_candidates_are_ignored() -> None:
    walk_only = _candidate(180, 18000, 0, steps=[{"travel_mode": "WALKING"}])
    transit = _candidate(
        55,
        600,
        1,
        steps=[
            {"travel_mode": "WALKING"},
            {"travel_mode": "TRANSIT", "transit_details": {"line": {"short_name": "BRT"}}},
        ],
    )
    prefs = TravelPreferences(accessibility_first=True, least_walk=True, fewest_transfers=True)
    result = choose_best_with_summary([walk_only, transit], prefs)
    assert result is not None
    assert result.candidate is transit


def test_no_transit_candidates_returns_none() -> None:
    walk_only = _candidate(120, 15000, 0, steps=[{"travel_mode": "WALKING"}])
    assert choose_best_with_summary([walk_only], TravelPreferences()) is None
