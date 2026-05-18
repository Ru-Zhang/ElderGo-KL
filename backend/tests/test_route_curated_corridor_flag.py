import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.preferences import TravelPreferences
from app.schemas.routes import PlaceInput, RouteRecommendationRequest
from app.services.google_maps_service import CandidateRoute


def _kjl_to_usj7_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "transit_details": {
            "departure_stop": {"name": "KLCC"},
            "arrival_stop": {"name": "USJ 7"},
            "line": {"short_name": "KJ", "vehicle": {"type": "SUBWAY"}},
        },
    }


def _brt_usj7_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "transit_details": {
            "departure_stop": {"name": "Stesen BRT USJ 7"},
            "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
            "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
        },
    }


def _walk_to_monash_step() -> dict:
    return {
        "travel_mode": "WALKING",
        "html_instructions": "Walk to Monash University Malaysia",
    }


def _ss18_brt_step() -> dict:
    return {
        "travel_mode": "TRANSIT",
        "transit_details": {
            "departure_stop": {"name": "Stesen BRT SS18"},
            "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
            "line": {"short_name": "BRT", "vehicle": {"type": "BUS"}},
        },
    }


def _candidate(steps: list[dict]) -> CandidateRoute:
    return CandidateRoute(
        duration_minutes=60,
        walking_distance_meters=400,
        transfers=2,
        steps=steps,
        polyline="abc",
        raw={},
    )


async def _recommend(origin: str, destination: str, steps: list[dict]):
    from app.services import route_service

    payload = RouteRecommendationRequest(
        origin=PlaceInput(display_name=origin),
        destination=PlaceInput(display_name=destination),
        departure_time="now",
        preferences=TravelPreferences(),
    )
    with patch.object(route_service.settings, "demo_mode", True):
        with patch.object(route_service, "get_route_cache") as mock_cache:
            mock_cache.return_value.get = AsyncMock(return_value=None)
            mock_cache.return_value.set = AsyncMock()
            with patch(
                "app.services.route_service.fetch_transit_candidates_lenient",
                new=AsyncMock(return_value=[_candidate(steps)]),
            ):
                with patch(
                    "app.services.klcc_monash_route_service.fetch_klcc_monash_brt_candidate",
                    new=AsyncMock(return_value=None),
                ):
                    return await route_service.recommend_route(payload)


def test_klcc_monash_usj7_corridor_uses_curated() -> None:
    result = asyncio.run(
        _recommend(
            "KLCC",
            "Monash University Malaysia",
            [
                {"travel_mode": "WALKING", "html_instructions": "Walk to KLCC"},
                _kjl_to_usj7_step(),
                {"travel_mode": "WALKING", "html_instructions": "Walk to USJ 7"},
                _brt_usj7_step(),
                {"travel_mode": "WALKING", "html_instructions": "Walk to Monash University Malaysia"},
            ],
        )
    )
    assert result.uses_curated_corridor is True
    assert any(step.curated_images for step in result.steps)


def test_kl_sentral_monash_via_usj7_uses_curated_on_corridor_legs() -> None:
    result = asyncio.run(
        _recommend(
            "KL Sentral",
            "Monash University Malaysia",
            [_kjl_to_usj7_step(), _brt_usj7_step(), _walk_to_monash_step()],
        )
    )
    assert result.uses_curated_corridor is True
    assert any("step-03" in image.path for image in result.steps[0].curated_images)
    assert any("step-04" in image.path for image in result.steps[1].curated_images)
    assert any("step-05" in image.path for image in result.steps[2].curated_images)


def test_klcc_monash_ss18_shortcut_no_curated() -> None:
    result = asyncio.run(
        _recommend(
            "KLCC",
            "Monash University Malaysia",
            [_ss18_brt_step()],
        )
    )
    assert result.uses_curated_corridor is False
    assert all(not step.curated_images for step in result.steps)
