"""In-process LRU cache for route recommendation responses."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.schemas.preferences import TravelPreferences
from app.schemas.routes import PlaceInput, RecommendedRoute, RouteRecommendationRequest
from app.services.departure_time_service import (
    is_departure_now,
    normalize_departure_key,
    resolve_departure_datetime,
)

KL_TZ = ZoneInfo("Asia/Kuala_Lumpur")
ROUTE_RANKING_CACHE_VERSION = "google-priority-fastest-v3-curated-lrt"


def _place_key(place: PlaceInput) -> str:
    if place.lat is not None and place.lon is not None:
        return f"{round(place.lat, 4)},{round(place.lon, 4)}"
    if place.google_place_id:
        return f"pid:{place.google_place_id}"
    return f"name:{place.display_name.strip().lower()}"


def _preferences_key(preferences: TravelPreferences) -> str:
    order = ",".join(preferences.priority_order)
    return (
        f"a{int(preferences.accessibility_first)}"
        f"w{int(preferences.least_walk)}"
        f"t{int(preferences.fewest_transfers)}"
        f"o:{order}"
    )


def _departure_bucket(departure_time: str) -> str:
    normalized = normalize_departure_key(departure_time)
    now = datetime.now(KL_TZ)

    if is_departure_now(normalized):
        bucket_minutes = 5
        minute = (now.minute // bucket_minutes) * bucket_minutes
        bucket = now.replace(minute=minute, second=0, microsecond=0)
        return f"now:{bucket.isoformat()}"

    if "T" in normalized or normalized not in {
        "morning_peak",
        "midday",
        "evening_peak",
        "night",
    }:
        try:
            resolved = resolve_departure_datetime(normalized).astimezone(KL_TZ)
        except (ValueError, TypeError):
            resolved = now
        bucket_minutes = 15
        minute = (resolved.minute // bucket_minutes) * bucket_minutes
        bucket = resolved.replace(minute=minute, second=0, microsecond=0)
        return f"iso:{bucket.isoformat()}"

    try:
        resolved = resolve_departure_datetime(normalized).astimezone(KL_TZ)
    except (ValueError, TypeError):
        resolved = now
    bucket_minutes = 15
    minute = (resolved.minute // bucket_minutes) * bucket_minutes
    bucket = resolved.replace(minute=minute, second=0, microsecond=0)
    return f"preset:{normalized}:{bucket.isoformat()}"


def build_route_cache_key(payload: RouteRecommendationRequest) -> str:
    departure = _departure_bucket(payload.departure_time)
    return "|".join(
        [
            ROUTE_RANKING_CACHE_VERSION,
            _place_key(payload.origin),
            _place_key(payload.destination),
            departure,
            _preferences_key(payload.preferences),
        ]
    )


def _cache_ttl_seconds(departure_time: str) -> int:
    settings = get_settings()
    if is_departure_now(normalize_departure_key(departure_time)):
        return min(settings.route_cache_ttl_seconds, 600)
    return settings.route_cache_ttl_seconds


def fresh_route_id(route: RecommendedRoute) -> RecommendedRoute:
    settings = get_settings()
    prefix = "demo_" if settings.demo_mode else "ephemeral_"
    return route.model_copy(update={"recommended_route_id": f"{prefix}{uuid.uuid4().hex[:12]}"})


@dataclass
class _CacheEntry:
    route: RecommendedRoute
    expires_at: float


class RouteRecommendationCache:
    def __init__(self, max_entries: int, default_ttl_seconds: int) -> None:
        self._max_entries = max_entries
        self._default_ttl_seconds = default_ttl_seconds
        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str, departure_time: str) -> RecommendedRoute | None:
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= time.monotonic():
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return fresh_route_id(entry.route)

    async def set(self, key: str, route: RecommendedRoute, departure_time: str) -> None:
        ttl = _cache_ttl_seconds(departure_time)
        async with self._lock:
            self._entries[key] = _CacheEntry(
                route=route.model_copy(deep=True),
                expires_at=time.monotonic() + ttl,
            )
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)


_route_cache: RouteRecommendationCache | None = None


def get_route_cache() -> RouteRecommendationCache:
    global _route_cache
    if _route_cache is None:
        settings = get_settings()
        _route_cache = RouteRecommendationCache(
            max_entries=settings.route_cache_max_entries,
            default_ttl_seconds=settings.route_cache_ttl_seconds,
        )
    return _route_cache
