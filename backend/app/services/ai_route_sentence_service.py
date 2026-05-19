"""Parse route sentences: origin/destination + departure time in one utterance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.services.departure_time_service import KL_TZ

DepartureValidation = Literal["ok", "past", "needs_date"]

# Re-export cleaning used by intent service
_PLACE_TIME_TAIL_PATTERNS = (
    re.compile(r"\s+at\s+the\s+(?:evening|morning|afternoon|night)\b.*$", re.I),
    re.compile(r"\s+in\s+the\s+(?:evening|morning|afternoon)\b.*$", re.I),
    re.compile(r"\s+(?:this|tomorrow)\s+(?:evening|morning|afternoon|night)\b.*$", re.I),
    re.compile(r"\s+(?:tonight|today)\b.*$", re.I),
    re.compile(r"\s+(?:晚上|早上|下午|傍晚|中午).*$"),
    re.compile(r"\s*,\s*(?:could|can|would|please|thank|recommend).*$", re.I),
    re.compile(
        r"\s+at\s+(?:(?:tom|tomorrow)|today|tonight)\s+(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b.*$",
        re.I,
    ),
    re.compile(r"\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b.*$", re.I),
    re.compile(r"\s+at\s+(?:(?:tom|tomorrow)|today)\b.*$", re.I),
)

ROUTE_FROM_TO_PATTERNS = (
    re.compile(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\bgo\s+from\s+(.+?)\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"从\s*(.+?)\s*到\s*([^中途?，。、]+?)(?:\s*中途|\?|$|，|。| and )"),
    re.compile(r"dari\s+(.+?)\s+ke\s+(.+?)(?:\?|$|,|\.| and )", re.I),
)
ROUTE_A_TO_B = re.compile(
    r"^(.+?)\s+to\s+(.+?)$",
    re.I,
)

_PLAN_ROUTE_INTENT_PHRASES = frozenset(
    {
        "i want to plan a route",
        "plan a route",
        "how do i plan a route in eldergo",
        "rancang laluan",
    }
)
_ENDPOINT_INTENT_WORDS = re.compile(
    r"\b(?:want|wanna|plan(?:ning)?|route|help|ticket|weather|station|travel|trip|journey|eldergo)\b",
    re.I,
)


def is_plan_route_intent_message(message: str) -> bool:
    """True when the user is starting plan-route flow, not naming two places."""
    lowered = message.strip().lower()
    if lowered in _PLAN_ROUTE_INTENT_PHRASES:
        return True
    return bool(
        re.search(r"\b(?:plan|planning)\s+(?:a\s+)?route\b", lowered)
        or re.search(r"\bi\s+want\s+to\s+plan\s+(?:a\s+)?route\b", lowered)
        or re.search(r"\brancang\s+laluan\b", lowered)
        or re.search(r"(?:我想|我要).*(?:规划|计划).*(?:路线|行程)", message)
    )


def _looks_like_place_endpoint(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned or is_plan_route_intent_message(cleaned):
        return False
    if _ENDPOINT_INTENT_WORDS.search(cleaned):
        return False
    from app.services.ai_route_parse_service import is_plausible_place_query

    return is_plausible_place_query(cleaned)
ROUTE_FROM_ONLY = (
    re.compile(r"\bfrom\s+(.+?)(?:\?|$|,|\.|\s+to\s)", re.I),
    re.compile(r"从\s*(.+?)(?:\?|$|，|。|\s*到)"),
    re.compile(r"dari\s+(.+?)(?:\?|$|,|\.|\s+ke\s)", re.I),
)
ROUTE_GO_TO_ONLY = (
    re.compile(r"\bgo\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\b(?:want|wanna)\s+to\s+go\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\b(?:want|wanna)\s+go\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\bheading\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\bget\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
)

_DEPARTURE_CHOICE_KEYS = ("now", "morning_peak", "midday", "evening_peak", "night")

_TIME_SIGNAL_PATTERNS = (
    re.compile(r"\b\d{1,2}\s*(?:am|pm)\b", re.I),
    re.compile(r"\b\d{1,2}:\d{2}\b"),
    re.compile(r"\b(?:tomorrow|today|tonight|tom|esok|明天|今天)\b", re.I),
    re.compile(r"\b(?:now|morning|evening|midday|noon|midnight|rush|peak)\b", re.I),
    re.compile(r"(?:现在|早上|下午|晚上|明天|几点)"),
)

_PREFERENCE_PATTERNS = (
    (re.compile(r"\baccessibility\s+first\b", re.I), "accessibility_first"),
    (re.compile(r"\bleast\s+walk(?:ing)?\b", re.I), "least_walk"),
    (re.compile(r"\bfewest\s+transfers?\b", re.I), "fewest_transfers"),
    (re.compile(r"无障碍优先", re.I), "accessibility_first"),
    (re.compile(r"少走路|少走", re.I), "least_walk"),
    (re.compile(r"少换乘", re.I), "fewest_transfers"),
)

_CONFIRM_YES_REPLIES = frozenset(
    {
        "yes",
        "y",
        "yeah",
        "yep",
        "ok",
        "okay",
        "sure",
        "confirm",
        "correct",
        "ya",
        "boleh",
        "是",
        "是的",
        "好",
        "好的",
        "可以",
        "对",
        "没错",
    }
)

_CONFIRM_NO_REPLIES = frozenset(
    {
        "no",
        "n",
        "nope",
        "not",
        "custom",
        "preferences",
        "preference",
        "set preference",
        "set preferences",
        "否",
        "不",
        "不要",
        "不用",
        "设置偏好",
        "偏好",
        "tidak",
    }
)

_PREFERENCES_DONE_REPLIES = frozenset(
    {
        "done",
        "ready",
        "finished",
        "continue",
        "go",
        "plan",
        "start",
        "完成",
        "好了",
        "继续",
        "开始",
        "规划",
        "siap",
        "sedia",
    }
)


@dataclass(frozen=True)
class RouteSentenceParse:
    origin: str | None
    destination: str | None
    departure: str | None
    route_message: str


def _normalize_tomorrow_aliases(message: str) -> str:
    return re.sub(r"\btom\b", "tomorrow", message, flags=re.I)


def sanitize_route_endpoint(raw: str | None) -> str | None:
    """Strip trailing time phrases and clean a single place name."""
    if not raw:
        return None
    cleaned = _clean_place_name(strip_time_suffix(raw.strip()))
    return cleaned if cleaned else None


def _clean_place_name(raw: str) -> str:
    cleaned = raw.strip().strip(".,!?;:")
    cleaned = re.sub(r"\s+", " ", cleaned)
    for pattern in _PLACE_TIME_TAIL_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip(".,!?;:")
    for sep in (" and ", " or ", " please ", " thanks "):
        lower = cleaned.lower()
        idx = lower.find(sep)
        if idx > 2:
            cleaned = cleaned[:idx].strip(".,!?;:")
    cleaned = re.sub(r"\s+please\b.*$", "", cleaned, flags=re.I).strip(".,!?;:")
    return cleaned[:120] if cleaned else ""


def strip_time_suffix(message: str) -> str:
    """Remove trailing departure-time phrases before place extraction."""
    text = message.strip()
    if not text:
        return text
    lowered = _normalize_tomorrow_aliases(text)
    for pattern in _PLACE_TIME_TAIL_PATTERNS[-3:]:
        lowered = pattern.sub("", lowered).strip(".,!?;:")
    for pattern in _PLACE_TIME_TAIL_PATTERNS[:-3]:
        lowered = pattern.sub("", lowered).strip(".,!?;:")
    return lowered if lowered else text


def has_departure_signal(message: str) -> bool:
    text = _normalize_tomorrow_aliases(message)
    return any(pattern.search(text) for pattern in _TIME_SIGNAL_PATTERNS)


def parse_custom_departure_iso(message: str) -> str | None:
    """Parse 'tomorrow 6am', 'at 1 pm', 'tom 1 pm' into ISO (Asia/Kuala_Lumpur)."""
    from datetime import datetime, timedelta

    lowered = _normalize_tomorrow_aliases(message.lower().strip())
    now = datetime.now(KL_TZ)
    target_date = None
    if re.search(r"\btomorrow\b|esok|明天", lowered):
        target_date = (now + timedelta(days=1)).date()
    elif re.search(r"\btoday\b|hari\s+ini|今天|tonight", lowered):
        target_date = now.date()

    time_match = re.search(
        r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(am|pm)?(?!\d)",
        lowered,
    )
    if not time_match:
        return None

    if target_date is None:
        target_date = now.date()

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    meridiem = time_match.group(3)
    if meridiem == "pm" and hour < 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    if not meridiem and hour <= 12 and re.search(r"\b(?:pm|petang|malam|晚上)\b", lowered):
        if hour < 12:
            hour += 12

    candidate = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        hour,
        minute,
        tzinfo=KL_TZ,
    )
    return candidate.isoformat()


def validate_departure_iso(iso: str, *, message: str = "") -> DepartureValidation:
    """Reject past clock times; flag vague calendar phrases without a resolved date."""
    from datetime import datetime

    from app.services.departure_time_service import normalize_departure_key

    preset_keys = frozenset({"now", "morning_peak", "midday", "evening_peak", "night"})

    normalized = normalize_departure_key(iso)
    if normalized in preset_keys:
        return "ok"
    try:
        dt = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KL_TZ)
        else:
            dt = dt.astimezone(KL_TZ)
    except ValueError:
        return "ok"

    now = datetime.now(KL_TZ)
    if dt <= now:
        return "past"

    lowered = _normalize_tomorrow_aliases((message or "").lower())
    vague_date = re.search(
        r"\b(?:next\s+week|next\s+month|later|sometime|某[天日]|下[周月])\b",
        lowered,
    )
    has_date_anchor = bool(
        re.search(r"\b(?:tomorrow|today|tonight|tom|esok|hari\s+ini|明天|今天)\b", lowered)
        or re.search(r"\d{4}-\d{2}-\d{2}", normalized)
    )
    if vague_date and not has_date_anchor:
        return "needs_date"
    return "ok"


_DEPARTURE_MAP = {
    "now": ("now", "sekarang", "现在", "此刻"),
    "morning_peak": (
        "morning_peak",
        "morning rush",
        "morning",
        "rush hour morning",
        "peak morning",
        "puncak pagi",
        "waktu puncak pagi",
        "早高峰",
        "早上高峰",
        "早上",
        "上午",
    ),
    "midday": ("midday", "mid day", "noon", "tengah hari", "中午", "午间"),
    "evening_peak": (
        "evening_peak",
        "evening rush",
        "evening",
        "rush hour evening",
        "peak evening",
        "puncak petang",
        "waktu puncak petang",
        "晚高峰",
        "傍晚高峰",
        "傍晚",
    ),
    "night": ("night", "malam", "last train", "before last", "晚上", "夜间", "末班"),
    "afternoon": ("afternoon", "petang", "下午"),
}


def parse_departure_time(message: str) -> str | None:
    """Return ISO string or preset departure key (now, morning_peak, …)."""
    from app.services.departure_time_service import LEGACY_KEY_MAP, normalize_departure_key

    custom_iso = parse_custom_departure_iso(message)
    if custom_iso:
        return custom_iso

    lowered = _normalize_tomorrow_aliases(message.lower().strip())
    if re.match(r"^\d+$", lowered):
        idx = int(lowered) - 1
        if 0 <= idx < len(_DEPARTURE_CHOICE_KEYS):
            return _DEPARTURE_CHOICE_KEYS[idx]
    if re.search(r"\b(?:rush|peak|puncak)\b.*\b(?:morning|pagi|am)\b", lowered) or re.search(
        r"\b(?:morning|pagi)\b.*\b(?:rush|peak|puncak)\b", lowered
    ):
        return "morning_peak"
    if re.search(r"\b(?:rush|peak|puncak)\b.*\b(?:evening|petang|pm)\b", lowered) or re.search(
        r"\b(?:evening|petang)\b.*\b(?:rush|peak|puncak)\b", lowered
    ):
        return "evening_peak"
    if re.search(r"\b(?:12\s*pm|noon|midday|tengah\s+hari|中午|正午)\b", lowered):
        return "midday"
    if re.search(r"\b(?:12\s*am|midnight|tengah\s+malam|午夜|凌晨)\b", lowered):
        return "night"
    # Do not map bare "2 pm" style clock times to midday — parse_custom_departure_iso handles those.
    if re.search(r"\b(?:5|6|7|8|9)\s*pm\b", lowered):
        return "evening_peak"
    if re.search(r"\b(?:9|10|11)\s*pm\b", lowered) or re.search(r"\blast\s+train\b", lowered):
        return "night"
    if re.search(r"\b(?:[6-9]\s*am|[6-9]am)\b", lowered):
        return "morning_peak"
    if re.search(r"下午|午间", message):
        return "midday"
    if re.search(r"早上|上午", message):
        return "morning_peak"
    if re.search(r"晚上|夜间|末班", message):
        return "night"
    if re.search(r"傍晚", message):
        return "evening_peak"
    if re.search(r"现在|马上|立刻", message):
        return "now"
    for value, keywords in _DEPARTURE_MAP.items():
        if any(keyword in lowered for keyword in keywords):
            mapped = LEGACY_KEY_MAP.get(value, value)
            return normalize_departure_key(mapped)
    return None


def extract_preference_hint(message: str) -> str | None:
    for pattern, key in _PREFERENCE_PATTERNS:
        if pattern.search(message):
            return key
    return None


def is_confirm_yes(message: str) -> bool:
    return message.strip().lower() in _CONFIRM_YES_REPLIES


def is_confirm_no(message: str) -> bool:
    return message.strip().lower() in _CONFIRM_NO_REPLIES


def is_preferences_done_reply(message: str) -> bool:
    lowered = message.strip().lower()
    return lowered in _PREFERENCES_DONE_REPLIES or extract_preference_hint(message) is not None


def has_explicit_departure_or_preference(message: str, slots: dict[str, str]) -> bool:
    if slots.get("departure_time") or slots.get("preference_hint"):
        return True
    if extract_preference_hint(message):
        return True
    if parse_departure_time(message):
        return True
    return False


def extract_route_endpoints(message: str) -> tuple[str | None, str | None]:
    text = strip_time_suffix(message.strip())
    if not text:
        return None, None

    for pattern in ROUTE_FROM_TO_PATTERNS:
        match = pattern.search(text)
        if match:
            origin = _clean_place_name(match.group(1))
            destination = _clean_place_name(match.group(2))
            if origin and destination and origin.lower() != destination.lower():
                return origin, destination

    if not re.search(r"\bfrom\b", text, re.I) and not re.search(r"\bdari\b", text, re.I):
        for pattern in ROUTE_GO_TO_ONLY:
            match = pattern.search(text)
            if match:
                dest_only_go = _clean_place_name(match.group(1))
                if dest_only_go:
                    return None, dest_only_go
        if not is_plan_route_intent_message(text):
            bare = ROUTE_A_TO_B.match(text.strip())
            if bare:
                origin = _clean_place_name(bare.group(1))
                destination = _clean_place_name(bare.group(2))
                if (
                    origin
                    and destination
                    and origin.lower() != destination.lower()
                    and not re.match(r"^(?:how|what|where|when|why)\b", origin, re.I)
                    and not re.search(r"\b(?:wanna|want\s+to|heading\s+to|get\s+to)\b", origin, re.I)
                    and _looks_like_place_endpoint(origin)
                    and _looks_like_place_endpoint(destination)
                ):
                    return origin, destination

    origin_only = None
    dest_only = None
    for pattern in ROUTE_FROM_ONLY:
        match = pattern.search(text)
        if match:
            origin_only = _clean_place_name(match.group(1))
            break
    if re.search(r"\bfrom\b", text, re.I) or re.search(r"\bdari\b", text, re.I):
        for pattern in ROUTE_GO_TO_ONLY:
            match = pattern.search(text)
            if match:
                candidate = _clean_place_name(match.group(1))
                if candidate and (not origin_only or candidate.lower() != origin_only.lower()):
                    dest_only = candidate
                break
        if not dest_only:
            to_match = re.search(r"\bto\s+(.+?)(?:\?|$|,|\.| and )", text, re.I)
            if to_match:
                candidate = _clean_place_name(to_match.group(1))
                if candidate and (not origin_only or candidate.lower() != origin_only.lower()):
                    dest_only = candidate

    if origin_only and dest_only:
        return origin_only, dest_only
    if origin_only:
        return origin_only, None
    if dest_only:
        return None, dest_only
    return None, None


def parse_route_sentence(message: str) -> RouteSentenceParse:
    route_message = strip_time_suffix(message)
    origin, destination = extract_route_endpoints(message)
    departure = parse_departure_time(message) if has_departure_signal(message) else None
    return RouteSentenceParse(
        origin=origin,
        destination=destination,
        departure=departure,
        route_message=route_message,
    )
