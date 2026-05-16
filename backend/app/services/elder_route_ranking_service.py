"""Deterministic Google-candidate ranking using user preference priority order."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from app.schemas.preferences import PreferenceFactor, TravelPreferences
from app.services.accessibility_annotation_service import quick_step_accessibility_risk
from app.services.google_maps_service import CandidateRoute, candidate_has_transit


RankingFactor = Literal["walk", "accessibility", "duration", "transfers"]


@dataclass
class RouteChoiceResult:
    candidate: CandidateRoute
    preference_summary_key: str
    ranking_primary_factor: RankingFactor = "duration"
    ranking_secondary_factor: RankingFactor = "walk"


def _accessibility_risk_counts(candidate: CandidateRoute) -> tuple[int, int]:
    unknown = 0
    not_supported = 0
    for step in candidate.steps:
        step_unknown, step_not_supported = quick_step_accessibility_risk(step)
        if step_not_supported:
            not_supported += 1
        elif step_unknown:
            unknown += 1
    return not_supported, unknown


def _active_priority(preferences: TravelPreferences) -> list[PreferenceFactor]:
    enabled = {
        "accessibility": preferences.accessibility_first,
        "walk": preferences.least_walk,
        "transfers": preferences.fewest_transfers,
    }
    return [factor for factor in preferences.priority_order if enabled[factor]]


def _metric(candidate: CandidateRoute, factor: PreferenceFactor) -> tuple[int, ...]:
    if factor == "accessibility":
        return _accessibility_risk_counts(candidate)
    if factor == "walk":
        return (candidate.walking_distance_meters,)
    return (candidate.transfers,)


def layered_key_elder(candidate: CandidateRoute, preferences: TravelPreferences) -> tuple:
    """Return a lexicographic key for one Google-returned route candidate."""
    active = _active_priority(preferences)
    if not active:
        not_supported, unknown = _accessibility_risk_counts(candidate)
        return (
            candidate.duration_minutes,
            candidate.walking_distance_meters,
            candidate.transfers,
            not_supported,
            unknown,
        )

    key: list[int] = []
    for factor in active:
        key.extend(_metric(candidate, factor))

    not_supported, unknown = _accessibility_risk_counts(candidate)
    key.extend(
        [
            candidate.duration_minutes,
            candidate.walking_distance_meters,
            candidate.transfers,
            not_supported,
            unknown,
        ]
    )
    return tuple(key)


def _summary_key(preferences: TravelPreferences) -> str:
    return "routePreferenceUserPriority" if _active_priority(preferences) else "routePreferenceFastest"


def _ranking_factors(preferences: TravelPreferences) -> tuple[RankingFactor, RankingFactor]:
    active = _active_priority(preferences)
    if not active:
        return "duration", "walk"
    primary: RankingFactor = "accessibility" if active[0] == "accessibility" else active[0]
    if len(active) >= 2:
        secondary: RankingFactor = "accessibility" if active[1] == "accessibility" else active[1]
    else:
        secondary = "duration"
    return primary, secondary


def _rank_pool(pool: list[CandidateRoute], preferences: TravelPreferences) -> RouteChoiceResult | None:
    transit = [candidate for candidate in pool if candidate_has_transit(candidate)]
    if not transit:
        return None
    ranked = sorted(transit, key=lambda candidate: layered_key_elder(candidate, preferences))
    primary, secondary = _ranking_factors(preferences)
    return RouteChoiceResult(
        candidate=ranked[0],
        preference_summary_key=_summary_key(preferences),
        ranking_primary_factor=primary,
        ranking_secondary_factor=secondary,
    )


def rank_candidates_for_elders(
    candidates: list[CandidateRoute],
    preferences: TravelPreferences,
    *,
    corridor_filter: Callable[[CandidateRoute], bool] | None = None,
) -> RouteChoiceResult | None:
    """Choose from Google-returned transit candidates using user priority order.

    corridor_filter is accepted for backward compatibility but intentionally
    ignored so preferences never force a route outside the Google candidate pool.
    """
    del corridor_filter
    return _rank_pool(candidates, preferences)


def choose_best_candidate(
    candidates: list[CandidateRoute],
    accessibility_first: bool = False,
    least_walk: bool = False,
    fewest_transfers: bool = False,
) -> CandidateRoute | None:
    prefs = TravelPreferences(
        accessibility_first=accessibility_first,
        least_walk=least_walk,
        fewest_transfers=fewest_transfers,
    )
    result = rank_candidates_for_elders(candidates, prefs)
    return result.candidate if result else None


def _dedupe_key(candidate: CandidateRoute) -> tuple:
    return (
        candidate.duration_minutes,
        candidate.walking_distance_meters,
        candidate.transfers,
        tuple(
            (
                step.get("travel_mode"),
                step.get("distance", {}).get("value"),
                step.get("duration", {}).get("value"),
                step.get("transit_details", {}).get("departure_stop", {}).get("name"),
                step.get("transit_details", {}).get("arrival_stop", {}).get("name"),
                step.get("transit_details", {}).get("line", {}).get("short_name")
                or step.get("transit_details", {}).get("line", {}).get("name"),
            )
            for step in candidate.steps
        ),
    )


def dedupe_candidates(candidates: list[CandidateRoute]) -> list[CandidateRoute]:
    seen: set[tuple] = set()
    unique: list[CandidateRoute] = []
    for candidate in candidates:
        key = _dedupe_key(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def align_composed_duration(
    best: CandidateRoute,
    all_candidates: list[CandidateRoute],
) -> CandidateRoute:
    """Kept as no-op compatibility now that ranking selects Google candidates."""
    del all_candidates
    return best
