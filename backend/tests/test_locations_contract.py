import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.api.v1.endpoints import locations


class FakeResult:
    def __init__(self, *, rows: list[dict] | None = None, row: dict | None = None) -> None:
        self._rows = rows or []
        self._row = row

    def fetchall(self) -> list[dict]:
        return self._rows

    def fetchone(self) -> dict | None:
        return self._row


class FakeConnection:
    def execute(self, query: str, params: dict | None = None) -> FakeResult:
        if "WHERE display_name ILIKE" in query:
            return FakeResult(
                rows=[
                    {
                        "location_id": "poi-1",
                        "location_type": "elevator",
                        "display_name": "Elevator A",
                        "accessibility_status": "not_supported",
                        "confidence": "low",
                        "lat": 3.14,
                        "lon": 101.68,
                    }
                ]
            )
        if "WHERE location_id = %(location_id)s" in query:
            return FakeResult(
                row={
                    "location_id": "poi-1",
                    "location_type": "elevator",
                    "source_id": "osm:123",
                    "display_name": "Elevator A",
                    "accessibility_status": "not_supported",
                    "confidence": "low",
                    "lat": 3.14,
                    "lon": 101.68,
                }
            )
        raise AssertionError(f"Unexpected query: {query}")


class FakeConnectionContext:
    def __enter__(self) -> FakeConnection:
        return FakeConnection()

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _fake_get_connection() -> FakeConnectionContext:
    return FakeConnectionContext()


class PopularFakeConnection:
    def execute(self, query: str, params: dict | None = None) -> FakeResult:
        if "FROM searchable_locations" in query and "WHERE location_type = 'rail_station'" in query:
            return FakeResult(
                rows=[
                    {
                        "location_id": "station:kl_sentral",
                        "location_type": "rail_station",
                        "display_name": "KL SENTRAL",
                        "accessibility_status": "supported",
                        "confidence": "high",
                        "lat": 3.13,
                        "lon": 101.68,
                    },
                    {
                        "location_id": "station:kl_sentral_redone",
                        "location_type": "rail_station",
                        "display_name": "KL SENTRAL - REDONE",
                        "accessibility_status": "supported",
                        "confidence": "high",
                        "lat": 3.14,
                        "lon": 101.69,
                    },
                    {
                        "location_id": "station:pasar_seni",
                        "location_type": "rail_station",
                        "display_name": "PASAR SENI",
                        "accessibility_status": "supported",
                        "confidence": "medium",
                        "lat": 3.14,
                        "lon": 101.7,
                    },
                ]
            )
        raise AssertionError(f"Unexpected query: {query}")


class PopularFakeConnectionContext:
    def __enter__(self) -> PopularFakeConnection:
        return PopularFakeConnection()

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _fake_popular_connection() -> PopularFakeConnectionContext:
    return PopularFakeConnectionContext()


class SearchDuplicateFakeConnection:
    def execute(self, query: str, params: dict | None = None) -> FakeResult:
        if "WHERE display_name ILIKE" in query:
            return FakeResult(
                rows=[
                    {
                        "location_id": "station:usj_7",
                        "location_type": "rail_station",
                        "display_name": "USJ 7",
                        "accessibility_status": "supported",
                        "confidence": "high",
                        "lat": 3.05,
                        "lon": 101.59,
                    },
                    {
                        "location_id": "station:usj7",
                        "location_type": "rail_station",
                        "display_name": "USJ7",
                        "accessibility_status": "supported",
                        "confidence": "high",
                        "lat": 3.05,
                        "lon": 101.59,
                    },
                    {
                        "location_id": "station:usj21",
                        "location_type": "rail_station",
                        "display_name": "USJ 21",
                        "accessibility_status": "supported",
                        "confidence": "high",
                        "lat": 3.02,
                        "lon": 101.58,
                    },
                ]
            )
        raise AssertionError(f"Unexpected query: {query}")


class SearchDuplicateFakeConnectionContext:
    def __enter__(self) -> SearchDuplicateFakeConnection:
        return SearchDuplicateFakeConnection()

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _fake_search_duplicate_connection() -> SearchDuplicateFakeConnectionContext:
    return SearchDuplicateFakeConnectionContext()


class StationDetailFakeConnection:
    def execute(self, query: str, params: dict | None = None) -> FakeResult:
        if "WHERE location_id = %(location_id)s" in query:
            return FakeResult(
                row={
                    "location_id": "station:kl_sentral",
                    "location_type": "rail_station",
                    "source_id": "station:kl_sentral",
                    "display_name": "KL SENTRAL",
                    "accessibility_status": "supported",
                    "confidence": "high",
                    "lat": 3.13,
                    "lon": 101.68,
                }
            )
        if "FROM station_group_members" in query:
            return FakeResult(
                rows=[
                    {"station_id": "rapid_rail:KJ15", "source_system": "rapid_rail"},
                    {"station_id": "rapid_rail:MR1", "source_system": "rapid_rail"},
                    {"station_id": "ktmb:19100", "source_system": "ktmb"},
                ]
            )
        if "FROM rail_station_routes" in query:
            return FakeResult(rows=[{"route_name": "KJL"}, {"route_name": "MRL"}, {"route_name": "KJL"}])
        if "JOIN accessibility_points point" in query:
            return FakeResult(
                row={
                    "wheelchair_access": True,
                    "shelter": True,
                    "covered": False,
                    "tactile_paving": False,
                    "bench": True,
                    "kerb": False,
                }
            )
        raise AssertionError(f"Unexpected query: {query}")


class StationDetailFakeConnectionContext:
    def __enter__(self) -> StationDetailFakeConnection:
        return StationDetailFakeConnection()

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _fake_station_detail_connection() -> StationDetailFakeConnectionContext:
    return StationDetailFakeConnectionContext()


class FailingConnectionContext:
    def __enter__(self):
        raise RuntimeError("database unavailable")

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _failing_get_connection() -> FailingConnectionContext:
    return FailingConnectionContext()


def test_locations_search_contract_accepts_extended_location_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(locations, "get_connection", _fake_get_connection)
    client = TestClient(app)

    response = client.get("/locations/search", params={"q": "elevator"})

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["type"] == "elevator"
    assert payload[0]["accessibility_status"] == "not_supported"


def test_locations_detail_contract_accepts_extended_location_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(locations, "get_connection", _fake_get_connection)
    client = TestClient(app)

    response = client.get("/locations/poi-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "elevator"
    assert payload["accessibility_status"] == "not_supported"


def test_popular_locations_dedupes_redone_name_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(locations, "get_connection", _fake_popular_connection)
    client = TestClient(app)

    response = client.get("/locations/popular")

    assert response.status_code == 200
    payload = response.json()
    returned_names = [item["name"] for item in payload]
    assert "KL SENTRAL" in returned_names
    assert "KL SENTRAL - REDONE" not in returned_names
    assert len(payload) == 2


def test_search_locations_dedupes_spacing_name_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(locations, "get_connection", _fake_search_duplicate_connection)
    client = TestClient(app)

    response = client.get("/locations/search", params={"q": "usj"})

    assert response.status_code == 200
    payload = response.json()
    returned_names = [item["name"] for item in payload]
    assert "USJ 7" in returned_names
    assert "USJ7" not in returned_names
    assert "USJ 21" in returned_names


def test_station_detail_uses_route_short_names_and_group_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(locations, "get_connection", _fake_station_detail_connection)
    client = TestClient(app)

    response = client.get("/locations/station:kl_sentral")

    assert response.status_code == 200
    payload = response.json()
    assert payload["accessibility_status"] == "supported"
    assert payload["routes"] == ["KJL", "MRL"]
    assert payload["known_facilities"] == ["Wheelchair access", "Shelter", "Bench"]
    assert payload["source_list"] == ["Rapid Rail", "KTMB"]


def test_search_returns_503_when_database_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(locations, "get_connection", _failing_get_connection)
    client = TestClient(app)

    response = client.get("/locations/search", params={"q": "kl"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Location data is temporarily unavailable."
