import asyncio
import time

from app.schemas.preferences import TravelPreferences
from app.schemas.routes import PlaceInput, RouteRecommendationRequest
from app.schemas.routes import (
    RecommendedRoute,
    RouteAccessibilityAnnotation,
    RouteStep,
)
from app.services.route_cache_service import (
    RouteRecommendationCache,
    build_route_cache_key,
    fresh_route_id,
)


def _sample_route(route_id: str = "ephemeral_test") -> RecommendedRoute:
    annotation = RouteAccessibilityAnnotation(
        status="unknown",
        message="test",
        source="test",
    )
    return RecommendedRoute(
        recommended_route_id=route_id,
        origin_name="A",
        destination_name="B",
        duration_minutes=20,
        transfers=1,
        walking_distance_meters=200,
        recommendation_reason="test",
        steps=[
            RouteStep(
                step_number=1,
                step_type="walking",
                instruction="walk",
                annotation=annotation,
            ),
        ],
    )


def _sample_payload(departure_time: str = "now") -> RouteRecommendationRequest:
    return RouteRecommendationRequest(
        origin=PlaceInput(display_name="Origin", lat=3.1, lon=101.6),
        destination=PlaceInput(display_name="Destination", lat=3.2, lon=101.7),
        departure_time=departure_time,
        preferences=TravelPreferences(
            accessibility_first=True,
            least_walk=False,
            fewest_transfers=False,
        ),
    )


def test_build_route_cache_key_differs_by_preferences():
    base = _sample_payload()
    other = base.model_copy(
        update={
            "preferences": TravelPreferences(
                accessibility_first=False,
                least_walk=True,
                fewest_transfers=False,
            )
        }
    )
    assert build_route_cache_key(base) != build_route_cache_key(other)


def test_build_route_cache_key_differs_by_priority_order():
    base = _sample_payload()
    other = base.model_copy(
        update={
            "preferences": TravelPreferences(
                accessibility_first=True,
                least_walk=True,
                fewest_transfers=False,
                priority_order=["walk", "accessibility", "transfers"],
            )
        }
    )
    assert build_route_cache_key(base) != build_route_cache_key(other)


def test_build_route_cache_key_includes_ranking_version():
    payload = _sample_payload()
    key = build_route_cache_key(payload)
    assert key.startswith("google-priority-fastest-v2|")


def test_build_route_cache_key_same_for_same_request():
    payload = _sample_payload()
    assert build_route_cache_key(payload) == build_route_cache_key(payload.model_copy())


def test_route_cache_hit_and_fresh_id():
    async def run() -> None:
        cache = RouteRecommendationCache(max_entries=4, default_ttl_seconds=60)
        payload = _sample_payload()
        key = build_route_cache_key(payload)
        route = _sample_route("ephemeral_original")

        await cache.set(key, route, payload.departure_time)
        hit = await cache.get(key, payload.departure_time)

        assert hit is not None
        assert hit.recommended_route_id != route.recommended_route_id
        assert hit.duration_minutes == route.duration_minutes

    asyncio.run(run())


def test_route_cache_expires():
    from unittest.mock import MagicMock, patch

    async def run() -> None:
        cache = RouteRecommendationCache(max_entries=4, default_ttl_seconds=1)
        payload = _sample_payload("midday")
        key = build_route_cache_key(payload)
        await cache.set(key, _sample_route(), payload.departure_time)

        time.sleep(1.1)
        assert await cache.get(key, payload.departure_time) is None

    settings = MagicMock()
    settings.route_cache_ttl_seconds = 1
    with patch("app.services.route_cache_service.get_settings", return_value=settings):
        asyncio.run(run())


def test_route_cache_lru_eviction():
    async def run() -> None:
        cache = RouteRecommendationCache(max_entries=2, default_ttl_seconds=60)
        payloads = [
            _sample_payload("now"),
            _sample_payload("midday"),
            _sample_payload("night"),
        ]
        keys = [build_route_cache_key(p) for p in payloads]

        for payload, key in zip(payloads, keys):
            await cache.set(key, _sample_route(key), payload.departure_time)

        assert await cache.get(keys[0], payloads[0].departure_time) is None
        assert await cache.get(keys[1], payloads[1].departure_time) is not None
        assert await cache.get(keys[2], payloads[2].departure_time) is not None

    asyncio.run(run())


def test_fresh_route_id_changes_only_id():
    route = _sample_route("ephemeral_a")
    refreshed = fresh_route_id(route)
    assert refreshed.recommended_route_id != route.recommended_route_id
    assert refreshed.duration_minutes == route.duration_minutes
