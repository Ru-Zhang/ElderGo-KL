"""Elder-first route ranking: walking → accessibility → duration → transfers (last)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.preferences import TravelPreferences
from app.services.accessibility_annotation_service import quick_step_accessibility_risk
from app.services.google_maps_service import CandidateRoute, candidate_has_transit


@dataclass
class RouteChoiceResult:
    candidate: CandidateRoute
    preference_summary_key: str
    ranking_primary_factor: str = "walk"
    ranking_secondary_factor: str = "duration"

_LONG_WALK_THRESHOLD_M = 800
_LONG_BUS_LEG_MINUTES = 25
_BASE_TRANSFERS_PENALTY = 100


@dataclass(frozen=True)
class ElderRankingWeights:
    walk: float = 1.0
    access: float = 1.0
    transfers_penalty: int = _BASE_TRANSFERS_PENALTY


def resolve_weights(preferences: TravelPreferences) -> ElderRankingWeights:
    """User toggles boost dimensions; exclusive single-pref uses stronger focus."""
    weights = ElderRankingWeights()
    exclusive_walk = preferences.least_walk and not preferences.accessibility_first
    exclusive_access = preferences.accessibility_first and not preferences.least_walk
    if exclusive_walk:
        walk, access = 4.0, 1.0
    elif exclusive_access:
        walk, access = 1.0, 4.0
    else:
        walk = weights.walk * (2.0 if preferences.least_walk else 1.0)
        access = weights.access * (2.0 if preferences.accessibility_first else 1.0)
    transfers_penalty = 0 if preferences.fewest_transfers else _BASE_TRANSFERS_PENALTY
    return ElderRankingWeights(walk=walk, access=access, transfers_penalty=transfers_penalty)


def uses_exclusive_preference_focus(preferences: TravelPreferences) -> bool:
    """True when only accessibility OR only least-walk is enabled (not both)."""
    return preferences.accessibility_first != preferences.least_walk


def _factor_label_from_key_index(index: int) -> str:
    if index == 0:
        return "walk"
    if index in (1, 2):
        return "accessibility"
    if index == 3:
        return "duration"
    if index == 4:
        return "duration"
    return "transfers"


def _ranking_factors(
    best_key: tuple,
    runner_key: tuple | None,
) -> tuple[str, str]:
    if runner_key is None:
        return "walk", "duration"
    primary: str | None = None
    secondary: str | None = None
    for index in range(min(len(best_key), len(runner_key))):
        if best_key[index] == runner_key[index]:
            continue
        label = _factor_label_from_key_index(index)
        if primary is None:
            primary = label
        elif secondary is None and label != primary:
            secondary = label
            break
    return primary or "walk", secondary or "duration"


def _accessibility_risk_counts(candidate: CandidateRoute) -> tuple[int, int]:
    unknown = 0
    not_supported = 0
    for step in candidate.steps:
        step_unknown, step_not_supported = quick_step_accessibility_risk(step)
        if step_not_supported:
            not_supported += 1
        elif step_unknown:
            unknown += 1
    return unknown, not_supported


def _is_brt_step(step: dict) -> bool:
    if step.get("travel_mode") != "TRANSIT":
        return False
    line = step.get("transit_details", {}).get("line", {})
    vehicle_type = line.get("vehicle", {}).get("type")
    line_name = (line.get("name") or line.get("short_name") or "").upper()
    return vehicle_type == "BUS" and "BRT" in line_name


def _long_non_brt_bus_penalty(candidate: CandidateRoute) -> int:
    for step in candidate.steps:
        if step.get("travel_mode") != "TRANSIT":
            continue
        if _is_brt_step(step):
            continue
        vehicle = step.get("transit_details", {}).get("line", {}).get("vehicle", {})
        if vehicle.get("type") != "BUS":
            continue
        minutes = step.get("duration", {}).get("value", 0) / 60
        if minutes >= _LONG_BUS_LEG_MINUTES:
            return 1
    return 0


def _effective_walk_meters(candidate: CandidateRoute, walk_weight: float) -> float:
    walk = float(candidate.walking_distance_meters)
    if walk > _LONG_WALK_THRESHOLD_M:
        walk += 500.0
    return walk * walk_weight


def _monash_corridor_flags(candidate: CandidateRoute) -> tuple[bool, bool]:
    """(uses_usj7_corridor, boards_brt_at_ss18/setia shortcut)."""
    from app.services.klcc_monash_route_service import (
        _candidate_boards_brt_at_ss18,
        uses_monash_corridor,
    )

    return uses_monash_corridor(candidate), _candidate_boards_brt_at_ss18(candidate)


def layered_key_elder(
    candidate: CandidateRoute,
    weights: ElderRankingWeights,
    preferences: TravelPreferences,
) -> tuple:
    unknown_steps, not_supported_steps = _accessibility_risk_counts(candidate)
    access_block = (
        not_supported_steps * weights.access,
        unknown_steps * weights.access,
    )
    walk_block = (_effective_walk_meters(candidate, weights.walk),)
    tail = (
        candidate.duration_minutes,
        _long_non_brt_bus_penalty(candidate),
        candidate.transfers + weights.transfers_penalty,
    )

    exclusive_walk = preferences.least_walk and not preferences.accessibility_first
    exclusive_access = preferences.accessibility_first and not preferences.least_walk

    if exclusive_access:
        usj7_corridor, ss18_board = _monash_corridor_flags(candidate)
        # Accessibility focus: avoid SS18/Setia shortcut; prefer USJ7 LRT+BRT corridor.
        return (
            1 if ss18_board else 0,
            *access_block,
            0 if usj7_corridor else 1,
            *walk_block,
            *tail,
        )

    if exclusive_walk:
        _, ss18_board = _monash_corridor_flags(candidate)
        # Walk/time focus: prefer Setia (SS18 BRT boarding) when walk is similar.
        return (
            *walk_block,
            0 if ss18_board else 1,
            *access_block,
            *tail,
        )

    return (*walk_block, *access_block, *tail)


def _preference_summary_key(
    preferences: TravelPreferences,
    best: CandidateRoute,
    ranked: list[CandidateRoute],
) -> str:
    active = [
        name
        for name, enabled in (
            ("accessibility", preferences.accessibility_first),
            ("walk", preferences.least_walk),
            ("transfers", preferences.fewest_transfers),
        )
        if enabled
    ]
    if not active:
        return "routePreferenceElderBaseline"

    if len(ranked) >= 2:
        second = ranked[1]
        if preferences.least_walk and best.walking_distance_meters > second.walking_distance_meters + 200:
            return "routePreferenceTradeoffWalking"
        if preferences.fewest_transfers and best.transfers > second.transfers:
            return "routePreferenceTradeoffTransfers"

    if preferences.accessibility_first:
        return "routePreferenceAccessibility"
    if preferences.fewest_transfers and not preferences.least_walk:
        return "routePreferenceFewestTransfers"
    if preferences.least_walk and not preferences.fewest_transfers:
        return "routePreferenceLeastWalk"
    return "routePreferenceElderBaseline"


def _rank_pool(
    pool: list[CandidateRoute],
    preferences: TravelPreferences,
) -> RouteChoiceResult | None:
    transit = [c for c in pool if candidate_has_transit(c)]
    if not transit:
        return None
    weights = resolve_weights(preferences)
    keyed = [(c, layered_key_elder(c, weights, preferences)) for c in transit]
    keyed.sort(key=lambda item: item[1])
    ranked = [c for c, _ in keyed]
    runner_key = keyed[1][1] if len(keyed) > 1 else None
    primary, secondary = _ranking_factors(keyed[0][1], runner_key)
    return RouteChoiceResult(
        candidate=ranked[0],
        preference_summary_key=_preference_summary_key(preferences, ranked[0], ranked),
        ranking_primary_factor=primary,
        ranking_secondary_factor=secondary,
    )


def rank_candidates_for_elders(
    candidates: list[CandidateRoute],
    preferences: TravelPreferences,
    *,
    corridor_filter: Callable[[CandidateRoute], bool] | None = None,
) -> RouteChoiceResult | None:
    """Rank transit candidates with fixed elder priority; optional corridor-first pool."""
    if corridor_filter is not None:
        corridor = [c for c in candidates if corridor_filter(c)]
        if corridor:
            result = _rank_pool(corridor, preferences)
            if result is not None:
                return result
    return _rank_pool(candidates, preferences)


def choose_best_candidate(
    candidates: list[CandidateRoute],
    accessibility_first: bool = False,
    least_walk: bool = False,
    fewest_transfers: bool = False,
) -> CandidateRoute | None:
    """Leg-level picker used by corridor composers (same elder baseline)."""
    prefs = TravelPreferences(
        accessibility_first=accessibility_first,
        least_walk=least_walk,
        fewest_transfers=fewest_transfers,
    )
    result = rank_candidates_for_elders(candidates, prefs)
    return result.candidate if result else None


def _dedupe_key(candidate: CandidateRoute) -> tuple:
    usj7_corridor, ss18_board = _monash_corridor_flags(candidate)
    composed = bool(isinstance(candidate.raw, dict) and candidate.raw.get("composed"))
    return (
        candidate.duration_minutes,
        candidate.walking_distance_meters,
        candidate.transfers,
        usj7_corridor,
        ss18_board,
        composed,
    )


def dedupe_candidates(candidates: list[CandidateRoute]) -> list[CandidateRoute]:
    """Drop near-duplicates but keep distinct Monash variants (USJ7 corridor vs SS18 shortcut)."""
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
    """Composed legs sum high; cap display duration to best direct Google estimate when lower."""
    if not isinstance(best.raw, dict) or not best.raw.get("composed"):
        return best
    direct = [
        c
        for c in all_candidates
        if not (isinstance(c.raw, dict) and c.raw.get("composed"))
    ]
    if not direct:
        return best
    google_min = min(c.duration_minutes for c in direct)
    if google_min >= best.duration_minutes:
        return best
    return CandidateRoute(
        duration_minutes=google_min,
        walking_distance_meters=best.walking_distance_meters,
        transfers=best.transfers,
        steps=best.steps,
        polyline=best.polyline,
        raw=best.raw,
    )
