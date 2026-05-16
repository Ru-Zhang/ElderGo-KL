"""Resolve departure time presets and ISO strings for KL public transit."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

KL_TZ = ZoneInfo("Asia/Kuala_Lumpur")
TRANSIT_SERVICE_START = time(6, 0)
TRANSIT_SERVICE_END = time(23, 30)

PRESET_KEYS = frozenset({"now", "morning_peak", "midday", "evening_peak", "night"})
PRESET_TIMES: dict[str, tuple[int, int]] = {
    "morning_peak": (7, 30),
    "midday": (12, 0),
    "evening_peak": (18, 0),
    "night": (21, 30),
}

LEGACY_KEY_MAP = {
    "morning": "morning_peak",
    "afternoon": "midday",
    "evening": "night",
}


def normalize_departure_key(value: str) -> str:
    cleaned = (value or "now").strip()
    lowered = cleaned.lower()
    if lowered in LEGACY_KEY_MAP:
        return LEGACY_KEY_MAP[lowered]
    if lowered in PRESET_KEYS:
        return lowered
    return cleaned


def is_departure_now(value: str) -> bool:
    return normalize_departure_key(value) == "now"


def _clamp_to_service_hours(dt: datetime, *, allow_after_last_service: bool = False) -> datetime:
    local = dt.astimezone(KL_TZ)
    current_time = local.time()
    if current_time < TRANSIT_SERVICE_START:
        return local.replace(
            hour=TRANSIT_SERVICE_START.hour,
            minute=TRANSIT_SERVICE_START.minute,
            second=0,
            microsecond=0,
        )
    if not allow_after_last_service and current_time > TRANSIT_SERVICE_END:
        next_day = local + timedelta(days=1)
        return next_day.replace(
            hour=TRANSIT_SERVICE_START.hour,
            minute=TRANSIT_SERVICE_START.minute,
            second=0,
            microsecond=0,
        )
    return local


def _next_preset_occurrence(hour: int, minute: int, *, from_dt: datetime | None = None) -> datetime:
    now = (from_dt or datetime.now(KL_TZ)).astimezone(KL_TZ)
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return _clamp_to_service_hours(candidate)


def resolve_departure_datetime(value: str) -> datetime:
    normalized = normalize_departure_key(value)

    if normalized == "now":
        return datetime.now(KL_TZ)

    if normalized in PRESET_TIMES:
        hour, minute = PRESET_TIMES[normalized]
        return _next_preset_occurrence(hour, minute)

    parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KL_TZ)
    # Custom ISO times are sent as-is after last service so Google can return no-transit.
    return _clamp_to_service_hours(parsed.astimezone(KL_TZ), allow_after_last_service=True)


def resolve_departure_epoch_seconds(value: str) -> int:
    if is_departure_now(value):
        return int(datetime.now(KL_TZ).timestamp())

    departure = resolve_departure_datetime(value)
    epoch = int(departure.timestamp())
    now_epoch = int(datetime.now(KL_TZ).timestamp())
    if epoch <= now_epoch:
        return now_epoch + 60
    return epoch


def departure_iso_after(value: str, extra_seconds: int) -> str:
    """ISO departure time for a later leg after prior segments complete."""
    base_epoch = resolve_departure_epoch_seconds(value)
    next_dt = datetime.fromtimestamp(base_epoch + max(0, extra_seconds), KL_TZ)
    return next_dt.isoformat()


def format_departure_display_label(value: str, language: str = "en") -> str:
    """Human-readable departure label for chat and UI summaries."""
    normalized = normalize_departure_key(value)
    dt = resolve_departure_datetime(value)
    locale = "ms-MY" if language == "ms" else "en-MY"
    time_part = dt.strftime("%I:%M %p").lstrip("0")

    if normalized == "now":
        today = {"en": "Now", "ms": "Sekarang", "zh": "现在"}[language]
        return f"{today}, {time_part}"

    preset_labels: dict[str, dict[str, str]] = {
        "morning_peak": {"en": "Morning peak", "ms": "Puncak pagi", "zh": "早高峰"},
        "midday": {"en": "Midday", "ms": "Tengah hari", "zh": "午间"},
        "evening_peak": {"en": "Evening peak", "ms": "Puncak petang", "zh": "晚高峰"},
        "night": {"en": "Night", "ms": "Malam", "zh": "夜间"},
    }
    if normalized in preset_labels:
        return preset_labels[normalized][language]

    now = datetime.now(KL_TZ)
    today_label = {"en": "Today", "ms": "Hari ini", "zh": "今天"}[language]
    tomorrow_label = {"en": "Tomorrow", "ms": "Esok", "zh": "明天"}[language]
    if dt.date() == now.date():
        return f"{today_label}, {time_part}"
    if dt.date() == (now + timedelta(days=1)).date():
        return f"{tomorrow_label}, {time_part}"
    day_part = dt.strftime("%a")
    return f"{day_part}, {time_part}"


def resolve_target_hour(value: str) -> int:
    normalized = normalize_departure_key(value)
    preset_hours = {
        "morning_peak": 7,
        "midday": 12,
        "evening_peak": 18,
        "night": 21,
    }
    if normalized in preset_hours:
        return preset_hours[normalized]
    if normalized == "now":
        return datetime.now(KL_TZ).hour
    return resolve_departure_datetime(value).hour
