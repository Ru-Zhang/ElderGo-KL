import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.navigation_waypoints_service import build_navigation_waypoints


def _transit_step(
    from_name: str,
    from_lat: float,
    from_lng: float,
    to_name: str,
    to_lat: float,
    to_lng: float,
) -> dict:
    return {
        "travel_mode": "TRANSIT",
        "transit_details": {
            "departure_stop": {"name": from_name, "location": {"lat": from_lat, "lng": from_lng}},
            "arrival_stop": {"name": to_name, "location": {"lat": to_lat, "lng": to_lng}},
        },
    }


def test_no_transit_steps_returns_empty() -> None:
    steps = [{"travel_mode": "WALKING", "start_location": {"lat": 3.1, "lng": 101.6}}]
    assert build_navigation_waypoints(steps) == []


def test_single_transit_leg_includes_boarding_stop() -> None:
    steps = [
        _transit_step("KLCC", 3.1579, 101.7118, "Ampang Park", 3.1595, 101.7132),
    ]
    waypoints = build_navigation_waypoints(steps)
    assert len(waypoints) == 2
    assert waypoints[0].name == "KLCC"
    assert waypoints[1].name == "Ampang Park"


def test_duplicate_stops_are_deduped() -> None:
    steps = [
        _transit_step("USJ 7", 3.0553, 101.5919, "USJ 7", 3.05531, 101.59191),
    ]
    waypoints = build_navigation_waypoints(steps)
    assert len(waypoints) == 1
    assert waypoints[0].name == "USJ 7"


def test_multi_leg_prioritizes_transfer_points_when_over_limit() -> None:
    steps = [
        _transit_step("KLCC", 3.1579, 101.7118, "KL Sentral", 3.1340, 101.6860),
        _transit_step("KL Sentral", 3.1340, 101.6860, "USJ 7", 3.0553, 101.5919),
        _transit_step("USJ 7", 3.0553, 101.5919, "SunU-Monash", 3.0654, 101.6016),
        _transit_step("SunU-Monash", 3.0654, 101.6016, "Monash", 3.0658, 101.6020),
    ]
    waypoints = build_navigation_waypoints(steps)
    assert len(waypoints) == 3
    names = [point.name for point in waypoints]
    assert "KL Sentral" in names
    assert "USJ 7" in names
    assert "SunU-Monash" in names


def test_respects_custom_max_waypoints() -> None:
    steps = [
        _transit_step("A", 1.0, 1.0, "B", 2.0, 2.0),
        _transit_step("B", 2.0, 2.0, "C", 3.0, 3.0),
    ]
    waypoints = build_navigation_waypoints(steps, max_waypoints=1)
    assert len(waypoints) == 1
