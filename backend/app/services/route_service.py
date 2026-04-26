import json
from datetime import UTC, datetime, timedelta
from uuid import UUID
import uuid

from app.core.config import get_settings
from app.schemas.routes import (
    RecommendedRoute,
    RouteAccessibilityAnnotation,
    RouteRecommendationRequest,
    RouteStep,
)
from app.services.database import get_connection
from app.services.google_maps_service import CandidateRoute, fetch_candidate_routes
from app.services.route_scoring_service import choose_best_candidate

settings = get_settings()


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


def _parse_optional_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(UUID(value))
    except (TypeError, ValueError):
        return None


def _parse_travel_time(value: str) -> datetime | None:
    if value == "now":
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return parsed.astimezone(UTC).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _annotation_status_for_db(value: str) -> str:
    if value in {"supported", "not_supported", "unknown"}:
        return value
    return "unknown"


def _annotation_confidence(status: str) -> str:
    if status == "supported":
        return "medium"
    return "low"


def _annotation_type(step_type: str) -> str:
    if step_type == "transit":
        return "station_wheelchair_accessibility"
    if step_type == "walking":
        return "nearby_accessibility_support"
    return "accessibility_unknown"


def _persist_route(payload: RouteRecommendationRequest, route: RecommendedRoute) -> str:
    anonymous_user_id = _parse_optional_uuid(payload.anonymous_user_id)
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=30)

    with get_connection() as conn:
        route_request_row = conn.execute(
            """
            INSERT INTO route_requests (
                anonymous_user_id,
                origin_text,
                destination_text,
                origin_geom,
                destination_geom,
                travel_time
            )
            VALUES (
                %(anonymous_user_id)s::uuid,
                %(origin_text)s,
                %(destination_text)s,
                CASE
                    WHEN %(origin_lon)s IS NULL OR %(origin_lat)s IS NULL THEN NULL
                    ELSE ST_SetSRID(ST_MakePoint(%(origin_lon)s, %(origin_lat)s), 4326)
                END,
                CASE
                    WHEN %(destination_lon)s IS NULL OR %(destination_lat)s IS NULL THEN NULL
                    ELSE ST_SetSRID(ST_MakePoint(%(destination_lon)s, %(destination_lat)s), 4326)
                END,
                %(travel_time)s
            )
            RETURNING route_request_id::text AS route_request_id
            """,
            {
                "anonymous_user_id": anonymous_user_id,
                "origin_text": payload.origin.display_name,
                "destination_text": payload.destination.display_name,
                "origin_lat": payload.origin.lat,
                "origin_lon": payload.origin.lon,
                "destination_lat": payload.destination.lat,
                "destination_lon": payload.destination.lon,
                "travel_time": _parse_travel_time(payload.departure_time),
            },
        ).fetchone()
        route_request_id = route_request_row["route_request_id"]

        recommended_row = conn.execute(
            """
            INSERT INTO recommended_routes (
                route_request_id,
                total_duration_min,
                walking_distance_m,
                transfer_count,
                summary_text,
                map_polyline,
                expires_at
            )
            VALUES (
                %(route_request_id)s::uuid,
                %(total_duration_min)s,
                %(walking_distance_m)s,
                %(transfer_count)s,
                %(summary_text)s,
                %(map_polyline)s,
                %(expires_at)s
            )
            RETURNING recommended_route_id::text AS recommended_route_id
            """,
            {
                "route_request_id": route_request_id,
                "total_duration_min": route.duration_minutes,
                "walking_distance_m": route.walking_distance_meters,
                "transfer_count": route.transfers,
                "summary_text": route.recommendation_reason,
                "map_polyline": route.map_polyline,
                "expires_at": expires_at,
            },
        ).fetchone()
        recommended_route_id = recommended_row["recommended_route_id"]

        for step in route.steps:
            step_row = conn.execute(
                """
                INSERT INTO route_steps (
                    recommended_route_id,
                    step_order,
                    travel_mode,
                    instruction_text,
                    google_transit_line,
                    duration_min,
                    walking_distance_m
                )
                VALUES (
                    %(recommended_route_id)s::uuid,
                    %(step_order)s,
                    %(travel_mode)s,
                    %(instruction_text)s,
                    %(google_transit_line)s,
                    %(duration_min)s,
                    %(walking_distance_m)s
                )
                RETURNING route_step_id::text AS route_step_id
                """,
                {
                    "recommended_route_id": recommended_route_id,
                    "step_order": step.step_number,
                    "travel_mode": step.step_type.upper(),
                    "instruction_text": step.instruction,
                    "google_transit_line": step.transit_line,
                    "duration_min": step.duration_minutes,
                    "walking_distance_m": step.distance_meters if step.step_type == "walking" else None,
                },
            ).fetchone()
            route_step_id = step_row["route_step_id"]
            annotation_status = _annotation_status_for_db(step.annotation.status)

            conn.execute(
                """
                INSERT INTO route_accessibility_annotations (
                    route_step_id,
                    target_type,
                    target_id,
                    annotation_type,
                    accessibility_status,
                    confidence,
                    source_list,
                    message,
                    distance_m
                )
                VALUES (
                    %(route_step_id)s::uuid,
                    %(target_type)s,
                    %(target_id)s,
                    %(annotation_type)s,
                    %(accessibility_status)s,
                    %(confidence)s,
                    %(source_list)s::jsonb,
                    %(message)s,
                    %(distance_m)s
                )
                """,
                {
                    "route_step_id": route_step_id,
                    "target_type": "google_hint",
                    "target_id": step.from_station or step.to_station,
                    "annotation_type": _annotation_type(step.step_type),
                    "accessibility_status": annotation_status,
                    "confidence": _annotation_confidence(annotation_status),
                    "source_list": json.dumps([step.annotation.source]),
                    "message": step.annotation.message,
                    "distance_m": step.distance_meters if step.step_type == "walking" else None,
                },
            )

        return recommended_route_id


async def recommend_route(payload: RouteRecommendationRequest) -> RecommendedRoute:
    candidates = await fetch_candidate_routes(payload.origin, payload.destination, payload.departure_time)
    best = choose_best_candidate(
        candidates,
        accessibility_first=payload.preferences.accessibility_first,
        least_walk=payload.preferences.least_walk,
        fewest_transfers=payload.preferences.fewest_transfers,
    )
    if best is None:
        raise ValueError("Google Maps did not return a usable route candidate.")
    recommendation = _route_from_candidate(payload, best)
    # In local/demo runs, route persistence can be unavailable; keep route planning usable.
    if settings.demo_mode:
        return recommendation.model_copy(update={"recommended_route_id": f"demo_{uuid.uuid4().hex[:12]}"})

    try:
        recommended_route_id = _persist_route(payload, recommendation)
    except Exception:
        recommended_route_id = f"ephemeral_{uuid.uuid4().hex[:12]}"
    return recommendation.model_copy(update={"recommended_route_id": recommended_route_id})
