from app.schemas.routes import (
    RecommendedRoute,
    RouteAccessibilityAnnotation,
    RouteRecommendationRequest,
    RouteStep,
)
from app.services.google_maps_service import CandidateRoute, fetch_candidate_routes
from app.services.route_scoring_service import choose_best_candidate


def build_demo_recommendation(payload: RouteRecommendationRequest) -> RecommendedRoute:
    return RecommendedRoute(
        recommended_route_id="demo_route_001",
        origin_name=payload.origin.display_name,
        destination_name=payload.destination.display_name,
        duration_minutes=25,
        transfers=1,
        walking_distance_meters=350,
        recommendation_reason="Demo recommendation pending live Google Maps scoring.",
        steps=[
            RouteStep(
                step_number=1,
                step_type="walking",
                instruction=f"Walk from {payload.origin.display_name} to the nearest station.",
                duration_minutes=5,
                distance_meters=350,
                annotation=RouteAccessibilityAnnotation(
                    status="unknown",
                    message="No verified walking accessibility data has been imported yet.",
                    source="demo_no_verified_local_data",
                ),
            ),
            RouteStep(
                step_number=2,
                step_type="transit",
                instruction="Take the recommended transit service.",
                duration_minutes=18,
                transit_line="Google Maps route pending",
                annotation=RouteAccessibilityAnnotation(
                    status="unknown",
                    message="Station accessibility will be checked after rail data import.",
                    source="demo_no_verified_station_profile",
                ),
            ),
            RouteStep(
                step_number=3,
                step_type="arrival",
                instruction=f"Arrive at {payload.destination.display_name}.",
                duration_minutes=2,
                distance_meters=100,
                annotation=RouteAccessibilityAnnotation(
                    status="unknown",
                    message="Destination accessibility has not been verified yet.",
                    source="demo_no_verified_local_data",
                ),
            ),
        ],
    )


def _clean_html_instruction(value: str | None) -> str:
    if not value:
        return "Continue to the next step."
    return (
        value.replace("<b>", "")
        .replace("</b>", "")
        .replace("<div style=\"font-size:0.9em\">", " ")
        .replace("</div>", "")
        .replace("&nbsp;", " ")
    )


def _step_from_google(step_number: int, google_step: dict) -> RouteStep:
    mode = google_step.get("travel_mode")
    step_type = "transit" if mode == "TRANSIT" else "walking"
    transit = google_step.get("transit_details", {})
    line = transit.get("line", {})
    return RouteStep(
        step_number=step_number,
        step_type=step_type,
        instruction=_clean_html_instruction(google_step.get("html_instructions")),
        duration_minutes=round(google_step.get("duration", {}).get("value", 0) / 60) or None,
        distance_meters=google_step.get("distance", {}).get("value"),
        transit_line=line.get("short_name") or line.get("name"),
        from_station=transit.get("departure_stop", {}).get("name"),
        to_station=transit.get("arrival_stop", {}).get("name"),
        annotation=RouteAccessibilityAnnotation(
            status="unknown",
            message="Accessibility annotation will be added from imported station and accessibility data.",
            source="google_route_pending_local_annotation",
        ),
    )


def _route_from_candidate(payload: RouteRecommendationRequest, candidate: CandidateRoute) -> RecommendedRoute:
    return RecommendedRoute(
        recommended_route_id="google_route_live",
        origin_name=payload.origin.display_name,
        destination_name=payload.destination.display_name,
        duration_minutes=candidate.duration_minutes,
        transfers=candidate.transfers,
        walking_distance_meters=candidate.walking_distance_meters,
        recommendation_reason="Selected from Google Maps transit candidates using ElderGo preference scoring.",
        map_polyline=candidate.polyline,
        steps=[
            _step_from_google(index + 1, step)
            for index, step in enumerate(candidate.steps)
        ],
    )


async def recommend_route(payload: RouteRecommendationRequest) -> RecommendedRoute:
    candidates = await fetch_candidate_routes(payload.origin, payload.destination, payload.departure_time)
    best = choose_best_candidate(candidates, payload.preferences.accessibility_first)
    if best is None:
        raise ValueError("Google Maps did not return a usable route candidate.")
    return _route_from_candidate(payload, best)
