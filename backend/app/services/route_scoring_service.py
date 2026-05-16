from dataclasses import dataclass

from app.schemas.preferences import TravelPreferences
from app.services.accessibility_annotation_service import quick_step_accessibility_risk
from app.services.google_maps_service import CandidateRoute, candidate_has_transit


@dataclass
class RouteChoiceResult:
    candidate: CandidateRoute
    preference_summary_key: str


def _accessibility_risk_counts(candidate: CandidateRoute) -> tuple[int, int]:
    """Fast risk counts from Google step JSON only (no DB) for candidate ranking."""
    unknown = 0
    not_supported = 0
    for step in candidate.steps:
        step_unknown, step_not_supported = quick_step_accessibility_risk(step)
        if step_not_supported:
            not_supported += 1
        elif step_unknown:
            unknown += 1
    return unknown, not_supported


def score_candidate(
    candidate: CandidateRoute,
    accessibility_first: bool = False,
    least_walk: bool = False,
    fewest_transfers: bool = False,
) -> float:
    unknown_steps, not_supported_steps = _accessibility_risk_counts(candidate)
    accessibility_weight = 50 if accessibility_first else 15
    walking_weight = 0.04 if least_walk else 0.02
    transfer_weight = 14 if fewest_transfers else 8
    accessibility_penalty = (
        not_supported_steps * 80 + unknown_steps * 25 if accessibility_first else unknown_steps * 5
    )
    return (
        candidate.duration_minutes
        + candidate.walking_distance_meters * walking_weight
        + candidate.transfers * transfer_weight
        + accessibility_penalty
    )


def _layered_key(
    candidate: CandidateRoute,
    *,
    accessibility_first: bool,
    least_walk: bool,
    fewest_transfers: bool,
) -> tuple:
    # Preference order matches the UI (top = highest priority):
    # accessibility → least walk → fewest transfers → duration tie-breaker.
    key_parts: list[float | int] = []
    unknown_steps, not_supported_steps = _accessibility_risk_counts(candidate)

    if accessibility_first:
        key_parts.extend([not_supported_steps, unknown_steps])
    if least_walk:
        key_parts.append(candidate.walking_distance_meters)
    if fewest_transfers:
        key_parts.append(candidate.transfers)

    key_parts.append(candidate.duration_minutes)
    return tuple(key_parts)


def choose_best_candidate(
    candidates: list[CandidateRoute],
    accessibility_first: bool = False,
    least_walk: bool = False,
    fewest_transfers: bool = False,
) -> CandidateRoute | None:
    transit_candidates = [c for c in candidates if candidate_has_transit(c)]
    if not transit_candidates:
        return None
    return min(
        transit_candidates,
        key=lambda c: _layered_key(
            c,
            accessibility_first=accessibility_first,
            least_walk=least_walk,
            fewest_transfers=fewest_transfers,
        ),
    )


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
        return "routePreferenceBalanced"

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
    return "routePreferenceBalanced"


def choose_best_with_summary(
    candidates: list[CandidateRoute],
    preferences: TravelPreferences,
) -> RouteChoiceResult | None:
    transit_candidates = [c for c in candidates if candidate_has_transit(c)]
    if not transit_candidates:
        return None

    # Precompute sort keys once — sorting used to re-run DB-heavy annotations per compare.
    keyed = [
        (
            candidate,
            _layered_key(
                candidate,
                accessibility_first=preferences.accessibility_first,
                least_walk=preferences.least_walk,
                fewest_transfers=preferences.fewest_transfers,
            ),
        )
        for candidate in transit_candidates
    ]
    keyed.sort(key=lambda item: item[1])
    ranked = [candidate for candidate, _ in keyed]
    best = ranked[0]
    summary_key = _preference_summary_key(preferences, best, ranked)
    return RouteChoiceResult(candidate=best, preference_summary_key=summary_key)
