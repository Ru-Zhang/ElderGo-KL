"""Extract Google Maps navigation waypoints from Directions API transit steps."""

from __future__ import annotations

import math

from app.schemas.routes import NavigationWaypoint

# Mobile Maps URLs support at most three intermediate waypoints.
MAX_MOBILE_WAYPOINTS = 3
# Treat stops within this distance as duplicates (~40 m).
_DEDUP_METERS = 40.0


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _stop_point(stop: dict | None) -> NavigationWaypoint | None:
    if not stop:
        return None
    location = stop.get("location") or {}
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None
    return NavigationWaypoint(lat=float(lat), lon=float(lng), name=stop.get("name"))


def _append_unique(points: list[NavigationWaypoint], candidate: NavigationWaypoint | None) -> None:
    if candidate is None:
        return
    if points and _haversine_meters(points[-1].lat, points[-1].lon, candidate.lat, candidate.lon) < _DEDUP_METERS:
        return
    points.append(candidate)


def _collect_transit_legs(google_steps: list[dict]) -> list[tuple[NavigationWaypoint | None, NavigationWaypoint | None]]:
    legs: list[tuple[NavigationWaypoint | None, NavigationWaypoint | None]] = []
    for step in google_steps:
        if step.get("travel_mode") != "TRANSIT":
            continue
        transit = step.get("transit_details") or {}
        legs.append((_stop_point(transit.get("departure_stop")), _stop_point(transit.get("arrival_stop"))))
    return legs


def _ordered_stop_candidates(legs: list[tuple[NavigationWaypoint | None, NavigationWaypoint | None]]) -> list[NavigationWaypoint]:
    if not legs:
        return []

    ordered: list[NavigationWaypoint] = []
    for index, (departure, arrival) in enumerate(legs):
        if index == 0 and departure is not None:
            _append_unique(ordered, departure)
        if arrival is not None:
            _append_unique(ordered, arrival)
        if index < len(legs) - 1:
            next_departure = legs[index + 1][0]
            if next_departure is not None:
                _append_unique(ordered, next_departure)

    return ordered


def _prioritize_for_mobile(
    legs: list[tuple[NavigationWaypoint | None, NavigationWaypoint | None]],
    ordered: list[NavigationWaypoint],
) -> list[NavigationWaypoint]:
    if len(ordered) <= MAX_MOBILE_WAYPOINTS:
        return ordered

    if len(legs) <= 1:
        return ordered[:MAX_MOBILE_WAYPOINTS]

    # Multi-leg: prefer transfer points (alight then board between segments).
    transfer_points: list[NavigationWaypoint] = []
    for index in range(len(legs) - 1):
        _, arrival = legs[index]
        next_departure, _ = legs[index + 1]
        if arrival is not None:
            _append_unique(transfer_points, arrival)
        if next_departure is not None:
            _append_unique(transfer_points, next_departure)

    if transfer_points:
        return transfer_points[:MAX_MOBILE_WAYPOINTS]

    return ordered[:MAX_MOBILE_WAYPOINTS]


def build_navigation_waypoints(
    google_steps: list[dict],
    *,
    max_waypoints: int = MAX_MOBILE_WAYPOINTS,
) -> list[NavigationWaypoint]:
    """Return up to ``max_waypoints`` intermediate stops for Google Maps deep links."""
    legs = _collect_transit_legs(google_steps)
    ordered = _ordered_stop_candidates(legs)
    prioritized = _prioritize_for_mobile(legs, ordered)
    return prioritized[:max_waypoints]
