import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.transit_direction_service import build_transit_line_direction


def test_kelana_jaya_towards_putra_heights() -> None:
    result = build_transit_line_direction(
        {
            "headsign": "Putra Heights",
            "line": {
                "name": "LRT Kelana Jaya Line",
                "short_name": "KJL",
                "vehicle": {"type": "SUBWAY"},
            },
        }
    )
    assert result == ("Gombak", "Putra Heights")


def test_brt_towards_sunway_setia_jaya() -> None:
    result = build_transit_line_direction(
        {
            "headsign": "Sunway-Setia Jaya",
            "line": {
                "name": "BRT Sunway Line",
                "short_name": "BRT",
                "vehicle": {"type": "BUS"},
            },
        }
    )
    assert result == ("USJ 7", "Sunway-Setia Jaya")


def test_brt_towards_usj7() -> None:
    result = build_transit_line_direction(
        {
            "headsign": "USJ 7",
            "line": {
                "name": "BRT Sunway Line",
                "vehicle": {"type": "BUS"},
            },
        }
    )
    assert result == ("Sunway-Setia Jaya", "USJ 7")


def test_brt_usj7_to_sunu_monash_prefers_stops_over_headsign() -> None:
    result = build_transit_line_direction(
        {
            "headsign": "USJ 7",
            "departure_stop": {"name": "Stesen BRT USJ7"},
            "arrival_stop": {"name": "Stesen BRT Sunu-Monash"},
            "line": {
                "name": "BRT Sunway Line",
                "short_name": "BRT",
                "vehicle": {"type": "BUS"},
            },
        }
    )
    assert result == ("USJ 7", "Sunway-Setia Jaya")


def test_missing_headsign_returns_none() -> None:
    assert build_transit_line_direction({"line": {"name": "LRT Kelana Jaya Line"}}) is None
