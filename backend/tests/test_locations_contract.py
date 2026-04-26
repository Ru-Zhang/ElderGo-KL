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
