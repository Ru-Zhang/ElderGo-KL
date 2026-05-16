import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.exceptions.route_errors import RouteUnavailableError
from app.schemas.preferences import TravelPreferences
from app.schemas.routes import PlaceInput, RouteRecommendationRequest
from app.services.google_maps_service import CandidateRoute, fetch_transit_candidates
from app.services.route_scoring_service import choose_best_with_summary


def _transit_candidate(duration: int = 50) -> CandidateRoute:
    return CandidateRoute(
        duration_minutes=duration,
        walking_distance_meters=400,
        transfers=1,
        steps=[
            {"travel_mode": "WALKING", "duration": {"value": 300}},
            {
                "travel_mode": "TRANSIT",
                "duration": {"value": duration * 60},
                "transit_details": {"line": {"short_name": "BRT", "vehicle": {"type": "BUS"}, "name": "BRT Sunway"}},
            },
        ],
        polyline="abc",
        raw={},
    )


async def _test_fetch_transit_candidates_raises_when_only_walking() -> None:
    walking_only = CandidateRoute(
        duration_minutes=120,
        walking_distance_meters=15000,
        transfers=0,
        steps=[{"travel_mode": "WALKING"}],
        polyline=None,
        raw={},
    )
    with patch(
        "app.services.google_maps_service._fetch_directions_candidates",
        new=AsyncMock(return_value=[walking_only]),
    ):
        with pytest.raises(RouteUnavailableError) as exc:
            await fetch_transit_candidates(
                PlaceInput(display_name="A"),
                PlaceInput(display_name="B"),
                "now",
            )
        assert exc.value.code == "no_transit_route"


def test_fetch_transit_candidates_raises_when_only_walking() -> None:
    asyncio.run(_test_fetch_transit_candidates_raises_when_only_walking())


def test_all_preferences_on_still_picks_transit_route() -> None:
    transit = _transit_candidate()
    prefs = TravelPreferences(accessibility_first=True, least_walk=True, fewest_transfers=True)
    choice = choose_best_with_summary([transit], prefs)
    assert choice is not None
    assert choice.candidate is transit


async def _test_recommend_route_uses_google_candidates_then_preferences() -> None:
    from app.services import route_service

    direct = _transit_candidate(duration=45)
    payload = RouteRecommendationRequest(
        origin=PlaceInput(display_name="USJ 7", lat=3.0553, lon=101.5919),
        destination=PlaceInput(display_name="Monash University", lat=3.06, lon=101.6),
        departure_time="2026-05-16T20:00:00+08:00",
        preferences=TravelPreferences(
            accessibility_first=True,
            least_walk=True,
            fewest_transfers=True,
        ),
    )

    with patch.object(route_service.settings, "demo_mode", True):
        with patch.object(route_service, "get_route_cache") as mock_cache:
            mock_cache.return_value.get = AsyncMock(return_value=None)
            mock_cache.return_value.set = AsyncMock()
            with patch(
                "app.services.route_service.fetch_transit_candidates_lenient",
                new=AsyncMock(return_value=[direct]),
            ) as mock_direct:
                result = await route_service.recommend_route(payload)

    mock_direct.assert_awaited_once()
    assert result.duration_minutes == 45
    assert result.preference_summary_key is not None


def test_recommend_route_uses_google_candidates_then_preferences() -> None:
    asyncio.run(_test_recommend_route_uses_google_candidates_then_preferences())


async def _test_recommend_route_uses_lenient_google_candidates() -> None:
    from app.services import route_service

    direct = _transit_candidate(duration=60)
    payload = RouteRecommendationRequest(
        origin=PlaceInput(display_name="KLCC"),
        destination=PlaceInput(display_name="Monash University"),
        departure_time="2026-05-16T20:00:00+08:00",
        preferences=TravelPreferences(),
    )

    with patch.object(route_service.settings, "demo_mode", True):
        with patch.object(route_service, "get_route_cache") as mock_cache:
            mock_cache.return_value.get = AsyncMock(return_value=None)
            mock_cache.return_value.set = AsyncMock()
            with patch(
                "app.services.route_service.fetch_transit_candidates_lenient",
                new=AsyncMock(return_value=[direct]),
            ) as mock_direct:
                result = await route_service.recommend_route(payload)

    mock_direct.assert_awaited_once()
    assert result.duration_minutes == 60


def test_recommend_route_uses_lenient_google_candidates() -> None:
    asyncio.run(_test_recommend_route_uses_lenient_google_candidates())
