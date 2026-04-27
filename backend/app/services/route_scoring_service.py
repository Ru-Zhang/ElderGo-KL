from app.services.google_maps_service import CandidateRoute


def score_candidate(
    candidate: CandidateRoute,
    accessibility_first: bool = False,
    least_walk: bool = False,
    fewest_transfers: bool = False,
) -> float:
    accessibility_weight = 50 if accessibility_first else 15
    walking_weight = 0.04 if least_walk else 0.02
    transfer_weight = 14 if fewest_transfers else 8
    unknown_accessibility_risk = 1
    return (
        candidate.duration_minutes
        + candidate.walking_distance_meters * walking_weight
        + candidate.transfers * transfer_weight
        + unknown_accessibility_risk * accessibility_weight
    )


def choose_best_candidate(
    candidates: list[CandidateRoute],
    accessibility_first: bool = False,
    least_walk: bool = False,
    fewest_transfers: bool = False,
) -> CandidateRoute | None:
    if not candidates:
        return None

    def layered_key(candidate: CandidateRoute) -> tuple:
        key_parts: list[float | int] = []

        # Layered decision:
        # 1) Apply user-selected priorities first.
        # 2) Use weighted score only as a tie-breaker.
        if accessibility_first:
            # In current data model accessibility is best approximated by lower walking burden
            # and fewer transfers, so prioritize these first.
            key_parts.extend([candidate.walking_distance_meters, candidate.transfers])
        if least_walk:
            key_parts.append(candidate.walking_distance_meters)
        if fewest_transfers:
            key_parts.append(candidate.transfers)

        key_parts.append(
            score_candidate(
                candidate,
                accessibility_first=accessibility_first,
                least_walk=least_walk,
                fewest_transfers=fewest_transfers,
            )
        )
        return tuple(key_parts)

    return min(candidates, key=layered_key)
