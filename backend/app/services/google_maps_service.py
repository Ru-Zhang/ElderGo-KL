from dataclasses import dataclass


@dataclass
class CandidateRoute:
    duration_minutes: int
    walking_distance_meters: int
    transfers: int
    raw: dict


async def fetch_candidate_routes() -> list[CandidateRoute]:
    """Placeholder for live Google Maps integration.

    The implementation must call Google Maps only when an API key is configured
    and should not persist rejected candidates permanently.
    """
    return []
