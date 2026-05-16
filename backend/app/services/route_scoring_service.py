"""Route scoring — delegates to elder-first ranking (backward-compatible exports)."""

from app.services.elder_route_ranking_service import (
    ElderRankingWeights,
    RouteChoiceResult,
    align_composed_duration,
    choose_best_candidate,
    dedupe_candidates,
    layered_key_elder,
    rank_candidates_for_elders,
    resolve_weights,
)
from app.services.google_maps_service import CandidateRoute, candidate_has_transit
from app.schemas.preferences import TravelPreferences


def choose_best_with_summary(
    candidates: list[CandidateRoute],
    preferences: TravelPreferences,
) -> RouteChoiceResult | None:
    return rank_candidates_for_elders(candidates, preferences)


def choose_best_for_monash_trip(
    candidates: list[CandidateRoute],
    preferences: TravelPreferences,
) -> RouteChoiceResult | None:
    from app.services.klcc_monash_route_service import uses_monash_corridor

    return rank_candidates_for_elders(
        candidates,
        preferences,
        corridor_filter=uses_monash_corridor,
    )
