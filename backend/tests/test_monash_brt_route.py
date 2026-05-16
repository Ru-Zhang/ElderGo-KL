import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
from unittest.mock import AsyncMock, patch

from app.schemas.routes import PlaceInput
from app.services.google_maps_service import CandidateRoute
from app.services.klcc_monash_route_service import (
    _origin_near_usj7,
    fetch_klcc_monash_brt_candidate,
    is_klcc_to_monash_route,
    is_monash_brt_route,
)


def test_monash_brt_route_for_usj_to_monash() -> None:
    origin = PlaceInput(display_name="USJ 1")
    destination = PlaceInput(display_name="Monash University Malaysia")
    assert is_monash_brt_route(origin, destination)
    assert is_klcc_to_monash_route(origin, destination)


def test_monash_brt_route_false_for_non_monash() -> None:
    origin = PlaceInput(display_name="USJ 1")
    destination = PlaceInput(display_name="KLCC")
    assert not is_monash_brt_route(origin, destination)


def test_origin_near_usj7_by_name_and_coords() -> None:
    assert _origin_near_usj7(PlaceInput(display_name="USJ 1"))
    assert _origin_near_usj7(PlaceInput(display_name="USJ 7 Station", lat=3.0553, lon=101.5919))
    assert not _origin_near_usj7(PlaceInput(display_name="KLCC", lat=3.157, lon=101.712))


async def _test_compose_skips_leg1_when_origin_at_usj7() -> None:
    brt_leg = CandidateRoute(
        duration_minutes=20,
        walking_distance_meters=100,
        transfers=0,
        steps=[
            {
                "travel_mode": "TRANSIT",
                "duration": {"value": 1200},
                "transit_details": {
                    "line": {"short_name": "BRT", "name": "BRT Sunway Line", "vehicle": {"type": "BUS"}}
                },
            }
        ],
        polyline="x",
        raw={},
    )
    final_leg = CandidateRoute(
        duration_minutes=8,
        walking_distance_meters=200,
        transfers=0,
        steps=[
            {"travel_mode": "WALKING", "duration": {"value": 300}},
            {
                "travel_mode": "TRANSIT",
                "duration": {"value": 480},
                "transit_details": {"line": {"short_name": "BRT", "vehicle": {"type": "BUS"}}},
            },
        ],
        polyline="y",
        raw={},
    )

    async def lenient_side_effect(origin, destination, departure_time):
        del departure_time, origin
        if destination.display_name.startswith("SunU"):
            return [brt_leg]
        if "Monash" in destination.display_name:
            return [final_leg]
        return []

    with patch(
        "app.services.klcc_monash_route_service.fetch_transit_candidates_lenient",
        new=AsyncMock(side_effect=lenient_side_effect),
    ) as mock_lenient:
        composed = await fetch_klcc_monash_brt_candidate(
            PlaceInput(display_name="USJ 7", lat=3.0553, lon=101.5919),
            PlaceInput(display_name="Monash University"),
            "2026-05-16T20:00:00+08:00",
        )

    assert composed is not None
    assert mock_lenient.await_count == 2


def test_compose_skips_leg1_when_origin_at_usj7() -> None:
    asyncio.run(_test_compose_skips_leg1_when_origin_at_usj7())
