from app.schemas.routes import (
    RecommendedRoute,
    RouteAccessibilityAnnotation,
    RouteRecommendationRequest,
    RouteStep,
)


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
