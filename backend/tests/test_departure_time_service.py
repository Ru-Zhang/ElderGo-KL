from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.departure_time_service import (
    KL_TZ,
    normalize_departure_key,
    resolve_departure_datetime,
    resolve_departure_epoch_seconds,
    resolve_target_hour,
)

KL = KL_TZ


def test_normalize_legacy_keys() -> None:
    assert normalize_departure_key("morning") == "morning_peak"
    assert normalize_departure_key("afternoon") == "midday"
    assert normalize_departure_key("evening") == "night"


def test_resolve_preset_hours() -> None:
    assert resolve_target_hour("morning_peak") == 7
    assert resolve_target_hour("midday") == 12
    assert resolve_target_hour("evening_peak") == 18
    assert resolve_target_hour("night") == 21


def test_resolve_iso_datetime() -> None:
    dt = resolve_departure_datetime("2026-05-16T12:30:00+08:00")
    assert dt.tzinfo == KL
    assert dt.hour == 12
    assert dt.minute == 30


def test_epoch_is_future() -> None:
    epoch = resolve_departure_epoch_seconds("midday")
    now = int(datetime.now(KL).timestamp())
    assert epoch >= now


def test_now_epoch() -> None:
    before = int(datetime.now(KL).timestamp())
    epoch = resolve_departure_epoch_seconds("now")
    after = int(datetime.now(KL).timestamp())
    assert before <= epoch <= after + 5


def test_custom_iso_after_last_service_not_clamped_to_morning() -> None:
    dt = resolve_departure_datetime("2026-05-16T23:50:00+08:00")
    assert dt.hour == 23
    assert dt.minute == 50
