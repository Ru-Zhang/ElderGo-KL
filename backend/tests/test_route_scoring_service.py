import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.preferences import TravelPreferences
from app.services.google_maps_service import CandidateRoute
from app.services.elder_route_ranking_service import (
    align_composed_duration,
    rank_candidates_for_elders,
)
from app.services.route_scoring_service import choose_best_for_monash_trip, choose_best_with_summary


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


def test_choose_best_prefers_less_walking_over_fewer_transfers() -> None:
    candidates = [
        _candidate(30, 900, 0),
        _candidate(32, 200, 3),
    ]
    prefs = TravelPreferences(fewest_transfers=True)
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.walking_distance_meters == 200


def test_choose_best_prefers_fewer_transfers_when_walk_and_time_equal() -> None:
    candidates = [
        _candidate(30, 200, 2),
        _candidate(30, 200, 0),
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


def test_monash_trip_prefers_corridor_over_direct_bus() -> None:
    bus = CandidateRoute(
        duration_minutes=50,
        walking_distance_meters=150,
        transfers=1,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "KL Sentral"},
                    "arrival_stop": {"name": "Monash University"},
                    "line": {"short_name": "770", "vehicle": {"type": "BUS"}},
                },
            }
        ],
        polyline=None,
        raw={},
    )
    corridor = CandidateRoute(
        duration_minutes=65,
        walking_distance_meters=400,
        transfers=3,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "KL Sentral"},
                    "arrival_stop": {"name": "USJ 7"},
                    "line": {"short_name": "KJ", "vehicle": {"type": "SUBWAY"}},
                },
            },
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "Stesen BRT USJ 7"},
                    "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                    "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}},
                },
            },
        ],
        polyline=None,
        raw={"composed": True},
    )
    prefs = TravelPreferences(accessibility_first=True, least_walk=True, fewest_transfers=True)
    result = choose_best_for_monash_trip([bus, corridor], prefs)
    assert result is not None
    assert result.candidate is corridor


def test_no_transit_candidates_returns_none() -> None:
    walk_only = _candidate(120, 15000, 0, steps=[{"travel_mode": "WALKING"}])
    assert choose_best_with_summary([walk_only], TravelPreferences()) is None


def test_elder_baseline_prefers_less_walking_when_all_prefs_off() -> None:
    candidates = [
        _candidate(30, 900, 0),
        _candidate(32, 200, 3),
    ]
    prefs = TravelPreferences(
        accessibility_first=False,
        least_walk=False,
        fewest_transfers=False,
    )
    result = choose_best_with_summary(candidates, prefs)
    assert result is not None
    assert result.candidate.walking_distance_meters == 200
    assert result.preference_summary_key == "routePreferenceElderBaseline"


def test_align_composed_duration_uses_google_when_lower() -> None:
    composed = CandidateRoute(
        duration_minutes=65,
        walking_distance_meters=400,
        transfers=3,
        steps=[_transit_step()],
        polyline=None,
        raw={"composed": True},
    )
    direct = _candidate(50, 500, 2)
    aligned = align_composed_duration(composed, [composed, direct])
    assert aligned.duration_minutes == 50


def test_exclusive_access_prefers_usj7_corridor_over_ss18() -> None:
    ss18 = CandidateRoute(
        duration_minutes=45,
        walking_distance_meters=120,
        transfers=1,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "Stesen BRT SS18"},
                    "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                    "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}},
                },
            }
        ],
        polyline=None,
        raw={},
    )
    usj7 = CandidateRoute(
        duration_minutes=55,
        walking_distance_meters=350,
        transfers=3,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "KL Sentral"},
                    "arrival_stop": {"name": "USJ 7"},
                    "line": {"short_name": "KJ", "vehicle": {"type": "SUBWAY"}},
                },
            },
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "Stesen BRT USJ 7"},
                    "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                    "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}},
                },
            },
        ],
        polyline=None,
        raw={"composed": True},
    )
    prefs = TravelPreferences(accessibility_first=True, least_walk=False, fewest_transfers=False)
    result = rank_candidates_for_elders([ss18, usj7], prefs)
    assert result is not None
    assert result.candidate is usj7


def test_exclusive_walk_prefers_ss18_over_usj7_corridor() -> None:
    ss18 = CandidateRoute(
        duration_minutes=45,
        walking_distance_meters=120,
        transfers=1,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "Stesen BRT SS18"},
                    "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                    "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
                },
            }
        ],
        polyline=None,
        raw={},
    )
    usj7 = CandidateRoute(
        duration_minutes=55,
        walking_distance_meters=350,
        transfers=3,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "Stesen BRT USJ 7"},
                    "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
                    "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
                },
            }
        ],
        polyline=None,
        raw={"composed": True},
    )
    prefs = TravelPreferences(accessibility_first=False, least_walk=True, fewest_transfers=False)
    result = rank_candidates_for_elders([ss18, usj7], prefs)
    assert result is not None
    assert result.candidate is ss18


def test_rank_candidates_corridor_filter_prefers_corridor_pool() -> None:
    bus = _candidate(50, 150, 1)
    corridor = CandidateRoute(
        duration_minutes=65,
        walking_distance_meters=400,
        transfers=3,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "transit_details": {
                    "departure_stop": {"name": "Stesen BRT USJ 7"},
                    "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}},
                },
            }
        ],
        polyline=None,
        raw={"composed": True},
    )

    def _is_corridor(c: CandidateRoute) -> bool:
        return bool(isinstance(c.raw, dict) and c.raw.get("composed"))

    prefs = TravelPreferences(accessibility_first=False, least_walk=False, fewest_transfers=False)
    without_filter = rank_candidates_for_elders([bus, corridor], prefs)
    with_filter = rank_candidates_for_elders(
        [bus, corridor],
        prefs,
        corridor_filter=_is_corridor,
    )
    assert without_filter is not None
    assert with_filter is not None
    assert without_filter.candidate is bus
    assert with_filter.candidate is corridor
