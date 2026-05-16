from unittest.mock import MagicMock, patch

from app.services.accessibility_annotation_service import (
    StationMatch,
    prefetch_station_matches,
)


def test_prefetch_station_matches_uses_single_connection():
    steps = [
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {
                    "name": "KLCC",
                    "location": {"lat": 3.157, "lng": 101.712},
                },
                "arrival_stop": {
                    "name": "Ampang Park",
                    "location": {"lat": 3.159, "lng": 101.714},
                },
            },
        },
        {
            "travel_mode": "TRANSIT",
            "transit_details": {
                "departure_stop": {
                    "name": "KLCC",
                    "location": {"lat": 3.157, "lng": 101.712},
                },
                "arrival_stop": {
                    "name": "Masjid Jamek",
                    "location": {"lat": 3.149, "lng": 101.697},
                },
            },
        },
    ]

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_conn
    mock_cm.__exit__.return_value = False

    with patch(
        "app.services.accessibility_annotation_service.get_connection",
        return_value=mock_cm,
    ):
        cache = prefetch_station_matches(steps)

    assert mock_cm.__enter__.call_count == 1
    assert len(cache) == 3
    assert all(key in cache for key in ("coord:3.157,101.712", "coord:3.159,101.714", "coord:3.149,101.697"))
