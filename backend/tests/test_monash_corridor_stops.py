import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.google_maps_service import CandidateRoute
from app.services.klcc_monash_route_service import (
    _candidate_arrives_at_usj7_lrt,
    _candidate_brt_usj7_to_sunu,
    _pick_klcc_to_usj7_lrt,
    _pick_usj7_to_sunu_brt,
    is_ss18_stop,
    is_usj7_stop,
)


def _lrt_step(*, departure: str, arrival: str) -> dict:
    return {
        "travel_mode": "TRANSIT",
        "duration": {"value": 1200},
        "transit_details": {
            "departure_stop": {"name": departure},
            "arrival_stop": {"name": arrival},
            "line": {"short_name": "KJ", "name": "Kelana Jaya Line", "vehicle": {"type": "SUBWAY"}},
        },
    }


def _brt_step(*, departure: str, arrival: str) -> dict:
    return {
        "travel_mode": "TRANSIT",
        "duration": {"value": 900},
        "transit_details": {
            "departure_stop": {"name": departure},
            "arrival_stop": {"name": arrival},
            "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}},
        },
    }


def _route(*steps: dict) -> CandidateRoute:
    return CandidateRoute(
        duration_minutes=30,
        walking_distance_meters=100,
        transfers=0,
        steps=list(steps),
        polyline="x",
        raw={},
    )


def test_stop_name_helpers() -> None:
    assert is_usj7_stop("Stesen LRT USJ 7")
    assert is_usj7_stop("Stesen BRT USJ 7")
    assert is_ss18_stop("Stesen BRT SS18")
    assert not is_usj7_stop("Stesen BRT SS18")


def test_klcc_leg_rejects_ss18_alight() -> None:
    wrong = _route(_lrt_step(departure="KLCC", arrival="SS18"))
    right = _route(_lrt_step(departure="KLCC", arrival="USJ 7"))
    assert not _candidate_arrives_at_usj7_lrt(wrong)
    assert _candidate_arrives_at_usj7_lrt(right)
    picked = _pick_klcc_to_usj7_lrt([wrong, right])
    assert picked is right


def test_brt_leg_prefers_usj7_not_ss18() -> None:
    wrong = _route(_brt_step(departure="Stesen BRT SS18", arrival="Stesen BRT Sunu-Monash"))
    right = _route(_brt_step(departure="Stesen BRT USJ 7", arrival="Stesen BRT Sunu-Monash"))
    assert not _candidate_brt_usj7_to_sunu(wrong)
    assert _candidate_brt_usj7_to_sunu(right)
    picked = _pick_usj7_to_sunu_brt([wrong, right])
    assert picked is right
