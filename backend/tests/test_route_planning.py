import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.routes import PlaceInput, RecommendedRoute, RouteRecommendationRequest, RouteStep
from app.services import accessibility_annotation_service as annotations
from app.services import route_service
from app.services.accessibility_annotation_service import (
    AccessibilityAnnotationResult,
    StationMatch,
)


class FakeResult:
    def __init__(self, row: dict | None = None) -> None:
        self._row = row

    def fetchone(self) -> dict | None:
        return self._row


class PersistConnection:
    def __init__(self) -> None:
        self.route_step_params: dict | None = None
        self.annotation_params: dict | None = None

    def execute(self, query: str, params: dict | None = None) -> FakeResult:
        if "INSERT INTO route_requests" in query:
            return FakeResult({"route_request_id": "11111111-1111-1111-1111-111111111111"})
        if "INSERT INTO recommended_routes" in query:
            return FakeResult({"recommended_route_id": "22222222-2222-2222-2222-222222222222"})
        if "INSERT INTO route_steps" in query:
            self.route_step_params = params
            return FakeResult({"route_step_id": "33333333-3333-3333-3333-333333333333"})
        if "INSERT INTO route_accessibility_annotations" in query:
            self.annotation_params = params
            return FakeResult()
        raise AssertionError(f"Unexpected query: {query}")


class PersistConnectionContext:
    def __init__(self, conn: PersistConnection) -> None:
        self.conn = conn

    def __enter__(self) -> PersistConnection:
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_transit_annotation_uses_local_station_profile(monkeypatch) -> None:
    station = StationMatch(
        station_id="rapid_rail:KJ15",
        station_name="KL Sentral",
        accessibility_status="supported",
        confidence="high",
        source_list=["rapid_rail_isOKU"],
        distance_m=12.4,
    )
    monkeypatch.setattr(annotations, "_find_station", lambda stop: station)

    result = annotations.annotate_google_step(
        {
            "travel_mode": "TRANSIT",
            "start_location": {"lat": 3.1, "lng": 101.6},
            "end_location": {"lat": 3.2, "lng": 101.7},
            "transit_details": {
                "departure_stop": {"name": "KL Sentral", "location": {"lat": 3.1, "lng": 101.6}},
                "arrival_stop": {"name": "Pasar Seni", "location": {"lat": 3.2, "lng": 101.7}},
            },
        }
    )

    assert result.annotation.status == "supported"
    assert result.annotation.source == "rapid_rail_isOKU"
    assert result.annotation_type == "station_wheelchair_accessibility"
    assert result.from_station_id == "rapid_rail:KJ15"
    assert result.target_id == "rapid_rail:KJ15"


def test_walking_annotation_uses_nearby_accessibility_point(monkeypatch) -> None:
    monkeypatch.setattr(
        annotations,
        "_walking_accessibility_result",
        lambda path_wkt: {
            "annotation_type": "nearby_sheltered_point",
            "point_id": "osm:node/1",
            "message": "Covered waiting area nearby: Covered walkway.",
            "distance_m": 8,
            "name": "Covered walkway",
            "lat": 3.1,
            "lon": 101.6,
            "accessibility_type": "wheelchair_stop",
            "wheelchair": "yes",
            "shelter": "yes",
            "covered": None,
        },
    )

    result = annotations.annotate_google_step(
        {
            "travel_mode": "WALKING",
            "start_location": {"lat": 3.1, "lng": 101.6},
            "end_location": {"lat": 3.2, "lng": 101.7},
            "polyline": {"points": "_p~iF~ps|U_ulLnnqC"},
        }
    )

    assert result.annotation.status == "supported"
    assert result.annotation.source == "accessibility_points"
    assert result.annotation_type == "nearby_sheltered_point"
    assert result.target_id == "osm:node/1"
    assert result.distance_m == 8
    assert result.accessibility_point is not None
    assert result.accessibility_point.lat == 3.1
    assert result.path_wkt and result.path_wkt.startswith("LINESTRING(")


def test_persist_route_writes_step_geometry_and_annotation_metadata(monkeypatch) -> None:
    conn = PersistConnection()
    monkeypatch.setattr(route_service, "get_connection", lambda: PersistConnectionContext(conn))

    annotation_result = AccessibilityAnnotationResult(
        annotation=annotations.unknown_annotation("No nearby static accessibility data found.", "test_source"),
        annotation_type="nearby_accessibility_support",
        confidence="low",
        target_type="walking_segment",
        target_id="segment-1",
        distance_m=25,
        start_wkt="POINT(101.6 3.1)",
        end_wkt="POINT(101.7 3.2)",
        path_wkt="LINESTRING(101.6 3.1, 101.7 3.2)",
    )
    step = RouteStep(
        step_number=1,
        step_type="walking",
        instruction="Walk to the station.",
        duration_minutes=4,
        distance_meters=280,
        annotation=annotation_result.annotation,
    )
    prepared = route_service.PreparedRecommendation(
        route=RecommendedRoute(
            recommended_route_id="google_route_live",
            origin_name="Origin",
            destination_name="Destination",
            duration_minutes=10,
            transfers=0,
            walking_distance_meters=280,
            recommendation_reason="Test route",
            steps=[step],
        ),
        prepared_steps=[route_service.PreparedRouteStep(step=step, annotation_result=annotation_result)],
    )
    payload = RouteRecommendationRequest(
        origin=PlaceInput(display_name="Origin", lat=3.1, lon=101.6),
        destination=PlaceInput(display_name="Destination", lat=3.2, lon=101.7),
    )

    route_id = route_service._persist_route(payload, prepared)

    assert route_id == "22222222-2222-2222-2222-222222222222"
    assert conn.route_step_params["start_wkt"] == "POINT(101.6 3.1)"
    assert conn.route_step_params["path_wkt"] == "LINESTRING(101.6 3.1, 101.7 3.2)"
    assert conn.annotation_params["annotation_type"] == "nearby_accessibility_support"
    assert conn.annotation_params["target_type"] == "walking_segment"
    assert conn.annotation_params["distance_m"] == 25
