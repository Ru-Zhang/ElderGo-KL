from app.services.google_maps_service import CandidateRoute


def score_candidate(candidate: CandidateRoute, accessibility_first: bool = False) -> float:
    accessibility_weight = 50 if accessibility_first else 15
    unknown_accessibility_risk = 1
    return (
        candidate.duration_minutes
        + candidate.walking_distance_meters * 0.02
        + candidate.transfers * 8
        + unknown_accessibility_risk * accessibility_weight
    )


def choose_best_candidate(candidates: list[CandidateRoute], accessibility_first: bool = False) -> CandidateRoute | None:
    if not candidates:
        return None
    return min(candidates, key=lambda candidate: score_candidate(candidate, accessibility_first))
