import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.weather_service import _analyze_rain_window, _select_forecast_item

KL = ZoneInfo("Asia/Kuala_Lumpur")


def _kl_item(hour: int, minute: int = 0, *, pop: float = 0, rain_mm: float = 0) -> dict:
    dt_kl = datetime(2026, 5, 16, hour, minute, tzinfo=KL)
    item: dict = {"dt": int(dt_kl.timestamp()), "main": {}, "pop": pop, "weather": [{"id": 800, "main": "Clear"}]}
    if rain_mm > 0:
        item["rain"] = {"3h": rain_mm}
        item["weather"] = [{"id": 500, "main": "Rain", "description": "light rain"}]
    return item


def test_select_forecast_near_custom_iso_not_on_the_hour() -> None:
    items = [_kl_item(21, 0), _kl_item(21, 30), _kl_item(22, 0)]
    selected, target_local = _select_forecast_item(
        items,
        "2026-05-16T21:30:00+08:00",
        timezone_offset=8 * 3600,
    )
    assert target_local is not None
    assert target_local.hour == 21
    assert target_local.minute == 30
    assert selected["dt"] == _kl_item(21, 30)["dt"]


def test_analyze_rain_window_merges_contiguous_wet_slots() -> None:
    items = [
        _kl_item(15, pop=0.1),
        _kl_item(18, pop=0.9, rain_mm=1.2),
        _kl_item(21, pop=0.85),
    ]
    selected = items[1]
    target = datetime(2026, 5, 16, 18, 30, tzinfo=KL)
    start, end, hours, peak = _analyze_rain_window(items, selected, target, 8 * 3600)
    assert start is not None
    assert end is not None
    assert hours == 6
    assert peak == 90
