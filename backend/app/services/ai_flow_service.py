"""Multi-turn guided chatbot flows (station, weather, plan route)."""

import asyncio
import json
import re
from typing import Literal

from fastapi import HTTPException

from app.schemas.ai import AIMessageRequest, ChatAction, ChatBlock
from app.services.chat_blocks_service import (
    blocks_ask_confirm_plan_route,
    blocks_ask_departure_time,
    blocks_ask_preferences_before_route,
    blocks_ask_use_defaults,
    blocks_outside_kv,
    blocks_weather_not_found,
    blocks_place_did_you_mean,
    blocks_place_not_found,
    blocks_place_not_found_for_slot,
    blocks_ask_route_destination,
    blocks_ask_route_origin,
    blocks_ask_station,
    blocks_ask_weather_location,
    blocks_error_short_input,
    blocks_invalid_departure,
    blocks_place_input_error,
    blocks_for_kv_weather_overview,
    blocks_for_station,
    blocks_for_weather,
    blocks_pick_retry,
    blocks_place_not_found,
    blocks_place_pick,
    blocks_route_ready,
    blocks_station_not_found,
    blocks_station_pick,
    blocks_from_plain_text,
    blocks_to_plain_text,
    blocks_invalid_departure,
    blocks_weather_not_found,
    dedupe_sources_blocks,
)
from app.schemas.weather import WeatherForecastRequest
from app.services.ai_intent_service import (
    IntentResult,
    WEATHER_PATTERNS,
    _format_weather_answer,
    _matches_any,
    detect_language,
)
from app.services.ai_route_parse_service import (
    classify_place_input,
    is_plausible_place_query,
    is_unclear_place_reply,
    lookup_known_kv_place,
    normalize_place_query,
    place_matches_user_query,
    place_ui_label,
    refine_place_query_for_slot,
    suggest_place_alias,
    try_gemini_route_pair,
    try_rule_route_pair,
)
from app.services.departure_time_service import KL_TZ, format_departure_display_label
from app.services.klang_valley_service import place_detail_in_kv
from app.services.locations_search_service import get_location_detail_by_id, search_station_locations
from app.services.places_service import search_places_kv
from app.services.weather_service import get_weather_forecast

FlowType = Literal["station_info", "weather", "plan_route"]

PLAN_ROUTE_STARTERS = (
    re.compile(r"\b(?:plan|planning)\s+(?:a\s+)?route\b", re.I),
    re.compile(r"\bi\s+want\s+to\s+plan\s+(?:a\s+)?route\b", re.I),
    re.compile(r"\brancang\s+laluan\b", re.I),
    re.compile(r"(?:我想|我要).*(?:规划|计划).*(?:路线|行程)"),
)
STATION_STARTERS = (
    re.compile(r"\b(?:station|stesen)\s+(?:info|detail|information)\b", re.I),
    re.compile(r"\btell\s+me\s+about\s+(?:a\s+)?station\b", re.I),
    re.compile(r"\b(?:which|what)\s+station\b", re.I),
    re.compile(r"(?:站点|车站).*(?:信息|详情)"),
)
WEATHER_STARTERS = (
    re.compile(r"\b(?:check|what(?:'s| is))\s+(?:the\s+)?weather\b", re.I),
    re.compile(r"\bweather\s+check\b", re.I),
    re.compile(r"\bsemak\s+cuaca\b", re.I),
    re.compile(r"(?:查|看).*(?:天气)"),
)

ASK_STATION = {
    "en": "Which station would you like information about?\nPlease type the station name.",
    "ms": "Stesen manakah yang anda mahu tahu?\nSila taip nama stesen.",
    "zh": "您想查询哪个站点？\n请输入站点名称。",
}
KV_WEATHER_CITY = "Kuala Lumpur"

WEATHER_BARE_TRIGGERS = frozenset(
    {
        "check the weather",
        "weather check",
        "semak cuaca",
        "查天气",
        "看天气",
        "what is the weather",
        "what's the weather",
    }
)

ASK_WEATHER_LOCATION = {
    "en": (
        "Which area in the Klang Valley would you like weather for?\n"
        "Please type a place (for example: Subang Jaya, KLCC, Petaling Jaya)."
    ),
    "ms": (
        "Kawasan manakah dalam Lembah Klang yang anda mahu cuaca?\n"
        "Sila taip tempat (contoh: Subang Jaya, KLCC, Petaling Jaya)."
    ),
    "zh": (
        "您想查询巴生谷哪个区域的天气？\n"
        "请输入地点（例如：Subang Jaya、KLCC、Petaling Jaya）。"
    ),
}
ASK_ROUTE_ORIGIN = {
    "en": "Where will you start from?\nPlease type your starting place in the Klang Valley.",
    "ms": "Dari mana anda akan bermula?\nSila taip tempat mula dalam Lembah Klang.",
    "zh": "您从哪里出发？\n请输入巴生谷内的出发地。",
}
ASK_ROUTE_DESTINATION = {
    "en": "Where would you like to go?\nPlease type your destination in the Klang Valley.",
    "ms": "Ke mana anda mahu pergi?\nSila taip destinasi dalam Lembah Klang.",
    "zh": "您要去哪里？\n请输入巴生谷内的目的地。",
}
ASK_DEPARTURE_TIME = {
    "en": (
        "When do you want to travel?\n"
        "- now\n"
        "- morning_peak (morning rush)\n"
        "- midday\n"
        "- evening_peak (evening rush)\n"
        "- night (before last trains)"
    ),
    "ms": (
        "Bila anda mahu bergerak?\n"
        "- sekarang (now)\n"
        "- morning_peak (waktu puncak pagi)\n"
        "- midday (tengah hari)\n"
        "- evening_peak (waktu puncak petang)\n"
        "- night (sebelum kereta terakhir)"
    ),
    "zh": (
        "您打算什么时候出发？\n"
        "- 现在 (now)\n"
        "- 早上 (morning)\n"
        "- 下午 (afternoon)\n"
        "- 晚上 (evening)"
    ),
}
STATION_NOT_FOUND = {
    "en": "I could not find that station.\nPlease check the spelling or try another station name.",
    "ms": "Saya tidak jumpa stesen itu.\nSila semak ejaan atau cuba nama stesen lain.",
    "zh": "找不到该站点。\n请检查拼写或尝试其他站点名称。",
}
WEATHER_NOT_FOUND = {
    "en": (
        "I could not find weather for that place.\n"
        "- Did you mean somewhere else in the Klang Valley?\n"
        "- Please check the spelling and try again."
    ),
    "ms": (
        "Saya tidak jumpa cuaca untuk tempat itu.\n"
        "- Adakah anda maksudkan tempat lain dalam Lembah Klang?\n"
        "- Sila semak ejaan dan cuba lagi."
    ),
    "zh": (
        "找不到该地点的天气。\n"
        "- 您是否指的是巴生谷内的其他地方？\n"
        "- 请检查拼写后重试。"
    ),
}
PICK_STATION = {
    "en": "I found a few stations. Please reply with the number (1, 2, 3) or the exact name:\n{options}",
    "ms": "Saya jumpa beberapa stesen. Sila balas dengan nombor (1, 2, 3) atau nama tepat:\n{options}",
    "zh": "找到多个站点，请回复编号（1、2、3）或准确名称：\n{options}",
}
STATION_PICK_RETRY = {
    "en": (
        "I couldn't match that to the list below.\n"
        "Please reply with a number (1, 2, 3) or copy the exact station name:\n{options}"
    ),
    "ms": (
        "Saya tidak dapat padankan dengan senarai di bawah.\n"
        "Sila balas dengan nombor (1, 2, 3) atau salin nama stesen tepat:\n{options}"
    ),
    "zh": "无法匹配下方列表。\n请回复编号（1、2、3）或复制准确站点名称：\n{options}",
}
PICK_PLACE = {
    "en": "I found a few places. Please reply with the number (1, 2, 3) or exact name:\n{options}",
    "ms": "Saya jumpa beberapa tempat. Sila balas dengan nombor (1, 2, 3) atau nama tepat:\n{options}",
    "zh": "找到多个地点，请回复编号（1、2、3）或准确名称：\n{options}",
}
PLACE_PICK_RETRY = {
    "en": (
        "I couldn't match that to the list below.\n"
        "Please reply with a number (1, 2, 3) or copy the exact place name:\n{options}"
    ),
    "ms": (
        "Saya tidak dapat padankan dengan senarai di bawah.\n"
        "Sila balas dengan nombor (1, 2, 3) atau salin nama tempat tepat:\n{options}"
    ),
    "zh": "无法匹配下方列表。\n请回复编号（1、2、3）或复制准确地点名称：\n{options}",
}
PLACE_INPUT_TOO_SHORT = {
    "en": (
        "That looks too short to be a place name.\n"
        "Please type a full location in the Klang Valley (for example: KL Sentral, Subang Jaya, KLCC)."
    ),
    "ms": (
        "Input itu terlalu pendek untuk nama tempat.\n"
        "Sila taip lokasi penuh dalam Lembah Klang (contoh: KL Sentral, Subang Jaya, KLCC)."
    ),
    "zh": "输入太短，不像地点名称。\n请输入巴生谷完整地点（例如：KL Sentral、Subang Jaya、KLCC）。",
}
PLACE_NOT_FOUND = {
    "en": (
        "I couldn't find that place in the Klang Valley.\n"
        "Please check the spelling or try a nearby landmark (for example: KL Sentral, Petaling Jaya)."
    ),
    "ms": (
        "Saya tidak jumpa tempat itu dalam Lembah Klang.\n"
        "Sila semak ejaan atau cuba mercu tanda berhampiran (contoh: KL Sentral, Petaling Jaya)."
    ),
    "zh": "在巴生谷找不到该地点。\n请检查拼写或尝试附近地标（例如：KL Sentral、Petaling Jaya）。",
}
INVALID_DEPARTURE = {
    "en": "Please choose: now, morning rush, midday, evening rush, or night.",
    "ms": "Sila pilih: sekarang, puncak pagi, tengah hari, puncak petang, atau malam.",
    "zh": "请选择：现在、早高峰、午间、晚高峰或夜间。",
}

DEPARTURE_MAP = {
    "now": ("now", "sekarang", "现在", "此刻"),
    "morning_peak": (
        "morning_peak",
        "morning rush",
        "rush hour morning",
        "peak morning",
        "puncak pagi",
        "waktu puncak pagi",
        "早高峰",
        "早上高峰",
    ),
    "midday": ("midday", "mid day", "noon", "tengah hari", "中午", "午间"),
    "evening_peak": (
        "evening_peak",
        "evening rush",
        "rush hour evening",
        "peak evening",
        "puncak petang",
        "waktu puncak petang",
        "晚高峰",
        "傍晚高峰",
    ),
    "night": ("night", "malam", "last train", "before last", "晚上", "夜间", "末班"),
    "morning": ("morning", "pagi", "早上", "上午"),
    "afternoon": ("afternoon", "petang", "下午"),
    "evening": ("evening", "傍晚"),
}


def _flow_error_result(
    error: str | list[ChatBlock],
    *,
    flow: FlowType | None,
    slots: dict[str, str] | None = None,
) -> IntentResult:
    if isinstance(error, list):
        return _flow_result(blocks=error, flow=flow, slots=slots)
    return _flow_result(error, flow=flow, slots=slots)


def _flow_result(
    answer: str | None = None,
    *,
    blocks: list[ChatBlock] | None = None,
    flow: FlowType | None = None,
    slots: dict[str, str] | None = None,
    actions: list[ChatAction] | None = None,
    in_scope: bool = True,
) -> IntentResult:
    if blocks:
        resolved_blocks = dedupe_sources_blocks(list(blocks))
        resolved_answer = (answer or "").strip() or blocks_to_plain_text(resolved_blocks)
    elif answer:
        resolved_answer = answer.strip()
        resolved_blocks = blocks_from_plain_text(resolved_answer)
    else:
        resolved_blocks = []
        resolved_answer = ""
    return IntentResult(
        intent="flow",
        answer=resolved_answer,
        answer_blocks=resolved_blocks,
        actions=actions or [],
        in_scope=in_scope,
        chat_flow=flow,
        flow_slots=slots or {},
        response_source="flow",
    )


def _is_plan_route_starter(message: str) -> bool:
    return any(pattern.search(message) for pattern in PLAN_ROUTE_STARTERS)


STATION_CHIP_MESSAGES = frozenset(
    {
        "tell me about a station",
        "station info",
        "station information",
    }
)

STATION_QUERY_ALIASES: dict[str, str] = {
    "usj7": "USJ 7",
    "usj 7": "USJ 7",
    "klcc": "KLCC",
    "kl sentral": "KL Sentral",
    "pasar seni": "Pasar Seni",
    "subang jaya": "SUBANG JAYA",
    "subang": "SUBANG JAYA",
}


def _normalize_station_query(query: str) -> str:
    cleaned = query.strip()
    if not cleaned:
        return cleaned
    return STATION_QUERY_ALIASES.get(cleaned.lower(), cleaned)


def _is_bare_flow_chip(message: str) -> bool:
    lowered = message.lower().strip()
    return (
        lowered in PLAN_BARE_TRIGGERS
        or lowered in WEATHER_BARE_TRIGGERS
        or lowered in STATION_CHIP_MESSAGES
    )


def _looks_like_station_query(message: str) -> bool:
    from app.services.ai_exploratory_poi_service import (
        extract_poi_category_term,
        is_area_poi_query,
        is_exploratory_poi_message,
    )

    if is_exploratory_poi_message(message) or is_area_poi_query(message):
        return False
    if extract_poi_category_term(message):
        return False

    from app.services.ai_route_sentence_service import extract_route_endpoints

    rule_origin, rule_dest = extract_route_endpoints(message)
    if rule_origin or rule_dest:
        return False

    lowered = message.lower()
    if re.search(
        r"\b(?:go\s+to|wanna|want\s+to|heading\s+to|get\s+to|nak\s+pergi)\b",
        lowered,
    ):
        return False

    cleaned = message.strip()
    if not cleaned or len(cleaned) > 28:
        return False
    lowered = cleaned.lower()
    if lowered in WEATHER_BARE_TRIGGERS | PLAN_BARE_TRIGGERS | STATION_CHIP_MESSAGES:
        return False
    if _explicit_flow_for_message(message) is not None:
        return False
    if re.match(r"^(from|to|go\s+to|dari|ke)\b", lowered):
        return False
    travel_hints = ("route", "travel", "plan", "weather", "ticket", "guide", "help", "how ")
    if any(hint in lowered for hint in travel_hints):
        return False
    if re.search(r"\b(?:in|near|around|area|附近)\b", lowered):
        return False
    return bool(re.match(r"^[A-Za-z0-9][A-Za-z0-9\s.'-]{0,26}$", cleaned))


def _explicit_flow_for_message(message: str) -> FlowType | None:
    """Detect when the user starts (or restarts) a guided flow via chip or phrase."""
    lowered = message.lower().strip()
    rule_origin, rule_dest = try_rule_route_pair(message)
    if rule_origin and rule_dest:
        return "plan_route"
    if lowered in PLAN_BARE_TRIGGERS or _is_plan_route_starter(message):
        return "plan_route"
    if lowered in WEATHER_BARE_TRIGGERS or _is_weather_starter(message) or _matches_any(
        message, WEATHER_PATTERNS
    ):
        return "weather"
    if lowered in STATION_CHIP_MESSAGES or _is_station_starter(message):
        return "station_info"
    return None


def _is_station_starter(message: str) -> bool:
    return any(pattern.search(message) for pattern in STATION_STARTERS)


def _is_weather_starter(message: str) -> bool:
    return _matches_any(message, WEATHER_PATTERNS) or any(
        pattern.search(message) for pattern in WEATHER_STARTERS
    )


def _starter_has_place(message: str) -> bool:
    lowered = message.lower().strip()
    bare = (
        "check the weather",
        "weather check",
        "semak cuaca",
        "tell me about a station",
        "station info",
        "i want to plan a route",
        "plan a route",
    )
    return lowered not in bare and len(lowered) > 12


_DEPARTURE_CHOICE_KEYS = ("now", "morning_peak", "midday", "evening_peak", "night")


def _parse_custom_departure_iso(message: str) -> str | None:
    """Parse 'tomorrow 6am' / 'today 3pm' / 'at 1 pm' into ISO departure for route API."""
    from app.services.ai_route_sentence_service import parse_custom_departure_iso

    return parse_custom_departure_iso(message)


def _parse_departure_time(message: str) -> str | None:
    from app.services.departure_time_service import LEGACY_KEY_MAP, normalize_departure_key

    custom_iso = _parse_custom_departure_iso(message)
    if custom_iso:
        return custom_iso

    lowered = message.lower().strip()
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
    if re.search(r"\b(?:1[0-1]|1[0-1]\s*pm|[2-4]\s*pm|[2-4]pm)\b", lowered):
        return "midday"
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
    for value, keywords in DEPARTURE_MAP.items():
        if any(keyword in lowered for keyword in keywords):
            mapped = LEGACY_KEY_MAP.get(value, value)
            return normalize_departure_key(mapped)
    return None


def _departure_input_is_invalid(message: str) -> bool:
    """True when the user clearly tried to set a time but we could not map it."""
    cleaned = message.strip()
    if not cleaned or _parse_departure_time(cleaned):
        return False
    if re.match(r"^\d+$", cleaned):
        return int(cleaned) > len(_DEPARTURE_CHOICE_KEYS)
    time_hints = (
        r"\b\d{1,2}\s*(?:am|pm)\b",
        r"\b\d{1,2}:\d{2}\b",
        r"\b(?:tomorrow|today|tonight|later)\b",
        r"(?:明天|后天|今天|几点)",
    )
    return any(re.search(pattern, cleaned, re.I) for pattern in time_hints)


def _place_input_blocks(message: str, language: str, *, slot: str | None = None) -> list[ChatBlock]:
    query = message
    if slot in ("origin", "destination"):
        query = refine_place_query_for_slot(message, slot)
    return blocks_place_input_error(classify_place_input(query), language)


def _extract_weather_place(message: str) -> str:
    lowered = message.lower().strip()
    if lowered in WEATHER_BARE_TRIGGERS:
        return ""
    at_match = re.search(
        r"(?:weather|forecast|cuaca|天气).{0,12}(?:at|in|for|near|di|de|ke|在|于)\s+([A-Za-z0-9][A-Za-z0-9\s.'-]{1,40})",
        message,
        re.I,
    )
    if at_match:
        return at_match.group(1).strip(" .,!?:;")
    return message.strip() if len(message.strip()) > 2 and lowered not in WEATHER_BARE_TRIGGERS else ""


def format_weather_report(forecast, language: str, *, region_label: str | None = None) -> str:
    """Format OpenWeather data for chat (no Gemini). Includes travel-friendly tips for adverse weather."""
    label = region_label or forecast.destination_name
    risk_hints = {
        "clear": {
            "en": "Weather looks comfortable for travel.",
            "ms": "Cuaca kelihatan sesuai untuk perjalanan.",
            "zh": "天气较适合出行。",
        },
        "rain": {
            "en": "Rain is possible — plan extra time and stay dry.",
            "ms": "Hujan mungkin berlaku — rancang masa tambahan dan kekal kering.",
            "zh": "可能下雨——请预留时间并注意防雨。",
        },
        "hot": {
            "en": "It may feel hot — travel slowly and drink water.",
            "ms": "Cuaca mungkin panas — bergerak perlahan dan minum air.",
            "zh": "可能较热——请慢行并补充水分。",
        },
        "storm": {
            "en": "Stormy conditions are possible — consider delaying non-essential trips.",
            "ms": "Cuaca ribut mungkin berlaku — pertimbangkan tangguh perjalanan tidak penting.",
            "zh": "可能有暴风雨——非必要出行可考虑延后。",
        },
        "unavailable": {
            "en": "Weather is temporarily unavailable.",
            "ms": "Cuaca tidak tersedia buat sementara waktu.",
            "zh": "天气暂不可用。",
        },
    }
    travel_tips = {
        "rain": {
            "en": "Travel tip: use covered walkways, hold handrails, and allow a few extra minutes.",
            "ms": "Tip perjalanan: guna laluan bertutup, pegang pemegang, dan beri masa tambahan.",
            "zh": "出行提示：尽量走有顶棚的路，扶好扶手，多留几分钟。",
        },
        "hot": {
            "en": "Travel tip: rest in shade or air-conditioning between legs if you feel tired.",
            "ms": "Tip perjalanan: berehat di tempat teduh atau berhawa dingin jika letih.",
            "zh": "出行提示：若感到疲劳，可在阴凉处或空调区休息。",
        },
        "storm": {
            "en": "Travel tip: ask station staff for help and prefer lifts over long outdoor walks.",
            "ms": "Tip perjalanan: minta bantuan staf stesen dan utamakan lif.",
            "zh": "出行提示：可向车站工作人员求助，优先使用电梯。",
        },
    }
    summary = risk_hints.get(forecast.risk_level, risk_hints["clear"])[language]
    advice_lines = "\n".join(f"- {line}" for line in forecast.senior_advice[:2])
    extra = travel_tips.get(forecast.risk_level, {}).get(language, "")
    extra_line = f"- {extra}\n" if extra else ""
    heading = {
        "en": f"Weather for {label} (Klang Valley)",
        "ms": f"Cuaca untuk {label} (Lembah Klang)",
        "zh": f"{label}（巴生谷）天气",
    }[language]
    return (
        f"{heading}\n"
        f"{summary}\n"
        f"- {forecast.temperature_c}°C, feels like {forecast.feels_like_c}°C.\n"
        f"- {forecast.weather_description.capitalize()}.\n"
        f"{advice_lines}\n"
        f"{extra_line}"
    ).strip()


def format_kv_weather_overview(forecast, language: str) -> str:
    intro = {
        "en": "Here is the current Klang Valley overview (Kuala Lumpur area):",
        "ms": "Ini ringkasan cuaca Lembah Klang (kawasan Kuala Lumpur):",
        "zh": "以下是巴生谷（吉隆坡一带）天气概览：",
    }[language]
    return f"{intro}\n\n{format_weather_report(forecast, language, region_label=KV_WEATHER_CITY)}"


def _format_station_answer(detail, language: str) -> str:
    status_labels = {
        "supported": {"en": "Supported", "ms": "Disokong", "zh": "支持"},
        "not_supported": {"en": "Not supported", "ms": "Tidak disokong", "zh": "不支持"},
        "unknown": {"en": "Unknown", "ms": "Tidak diketahui", "zh": "未知"},
    }
    status = status_labels.get(detail.accessibility_status, status_labels["unknown"])[language]
    routes = ", ".join(detail.routes) if detail.routes else "-"
    facilities = ", ".join(detail.known_facilities or detail.station_facilities or []) or "-"
    hours = detail.station_hours_summary or "-"
    address = detail.station_address or "-"

    if language == "ms":
        return (
            f"Maklumat stesen (dari data Stesen ElderGo KL) untuk {detail.name}:\n"
            f"- Kebolehcapaian: {status}\n"
            f"- Laluan: {routes}\n"
            f"- Kemudahan: {facilities}\n"
            f"- Waktu operasi: {hours}\n"
            f"- Alamat: {address}\n"
            "Tekan butang di bawah untuk buka halaman butiran stesen penuh."
        )
    if language == "zh":
        return (
            f"{detail.name} 站点信息（来自 ElderGo KL 站点数据）：\n"
            f"- 无障碍：{status}\n"
            f"- 线路：{routes}\n"
            f"- 设施：{facilities}\n"
            f"- 营业时间：{hours}\n"
            f"- 地址：{address}\n"
            "点击下方按钮打开完整站点详情页。"
        )
    return (
        f"Station information (from ElderGo KL Stations data) for {detail.name}:\n"
        f"- Accessibility: {status}\n"
        f"- Lines: {routes}\n"
        f"- Facilities: {facilities}\n"
        f"- Opening hours: {hours}\n"
        f"- Address: {address}\n"
        "Tap the button below to open the full station detail page."
    )


def _candidate_lines(candidates: list[dict], language: str) -> str:
    lines = []
    for index, item in enumerate(candidates[:3], start=1):
        lines.append(f"{index}. {item.get('label') or item['name']}")
    return "\n".join(lines)


def _place_candidate_key(place) -> str:
    """Group near-duplicate Google Places rows (e.g. multiple KL Sentral addresses)."""
    raw = (place.name or place.display_name or "").strip().lower()
    raw = re.sub(r"\s+", " ", raw)
    if "kl sentral" in raw or "kuala lumpur sentral" in raw:
        return "kl sentral"
    head = raw.split(",")[0].strip()
    head = re.sub(r"\s*[-–—]\s*redone$", "", head, flags=re.I)
    return head[:80]


def _place_candidate_label(place) -> str:
    if place.name:
        return place.name.strip()
    return (place.display_name or "").split(",")[0].strip()


def _dedupe_kv_places(places: list, limit: int = 3) -> list:
    deduped: list = []
    seen: set[str] = set()
    for place in places:
        key = _place_candidate_key(place)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(place)
        if len(deduped) >= limit:
            break
    return deduped


def _resolved_place_dict(place, user_query: str) -> dict:
    """Full address in name (for geocoding); short label for chat + route UI."""
    google_name = (place.name or "").strip() or None
    canonical = normalize_place_query(user_query)
    return {
        "name": place.display_name,
        "label": place_ui_label(
            user_query,
            google_name=google_name,
            canonical_name=canonical or _place_candidate_label(place),
        ),
        "lat": place.lat,
        "lon": place.lon,
        "google_place_id": place.google_place_id,
    }


def _route_place_label(place: dict) -> str:
    return (place.get("label") or place.get("name") or "").strip()


def _places_to_candidates(places: list, *, user_query: str = "") -> list[dict]:
    return [
        _resolved_place_dict(place, user_query or _place_candidate_label(place))
        for place in places
    ]


def _match_named_candidate(message: str, candidates: list[dict]) -> dict | None:
    choice = message.strip()
    if not choice or not candidates:
        return None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
    lowered = choice.lower()
    for item in candidates:
        for field in ("label", "name"):
            name = (item.get(field) or "").strip()
            if not name:
                continue
            name_lower = name.lower()
            if name_lower == lowered or lowered in name_lower or name_lower in lowered:
                return item
    return None


def _try_pick_candidate_from_slots(
    message: str, slots: dict[str, str], candidate_key: str
) -> tuple[dict | None, dict[str, str]]:
    candidates = _load_candidates(slots, candidate_key)
    if not candidates:
        return None, slots
    picked = _match_named_candidate(message, candidates)
    if not picked:
        return None, slots
    updated = {k: v for k, v in slots.items() if k != candidate_key}
    updated.pop("origin_pending", None)
    updated.pop("destination_pending", None)
    return picked, updated


def _load_candidates(slots: dict[str, str], key: str) -> list[dict]:
    raw = slots.get(key, "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def _save_candidates(slots: dict[str, str], key: str, candidates: list[dict]) -> dict[str, str]:
    updated = dict(slots)
    updated[key] = json.dumps(candidates)
    return updated


def _resolved_place_from_known(known: dict[str, object], user_query: str) -> dict:
    name = str(known.get("name") or user_query)
    return {
        "name": str(known.get("formatted_address") or name),
        "label": str(known.get("label") or place_ui_label(user_query, canonical_name=name)),
        "lat": known["lat"],
        "lon": known["lon"],
        "google_place_id": known["google_place_id"],
    }


async def _resolve_place_by_query(
    query: str,
    language: str,
    *,
    slot: Literal["origin", "destination"] | None = None,
    slots: dict[str, str] | None = None,
) -> tuple[dict | None, dict[str, str], str | list[ChatBlock] | None]:
    """Resolve a place; when several KV matches exist, return candidate slots to pick from."""
    from app.services.ai_route_sentence_service import sanitize_route_endpoint

    user_query = sanitize_route_endpoint(query) or query.strip()
    base_slots = dict(slots or {})
    issue = classify_place_input(user_query)
    if issue != "ok":
        return None, base_slots, blocks_place_input_error(issue, language)

    def _not_found() -> list[ChatBlock]:
        if slot:
            return blocks_place_not_found_for_slot(slot, user_query, language)
        return blocks_place_not_found(language)

    from app.services.ai_route_parse_service import is_broad_area_place_query

    known = lookup_known_kv_place(user_query)
    if known is not None and not (slot and is_broad_area_place_query(user_query)):
        return _resolved_place_from_known(known, user_query), base_slots, None
    normalized = normalize_place_query(user_query)
    places = await search_places_kv(normalized, limit=8)
    kv_places = _dedupe_kv_places([p for p in places if place_detail_in_kv(p)], limit=3)
    if places and not kv_places:
        return None, base_slots, blocks_outside_kv(language)
    if not kv_places:
        suggestion = suggest_place_alias(user_query)
        if suggestion:
            label = place_ui_label(user_query, canonical_name=suggestion)
            return None, base_slots, blocks_place_did_you_mean(label, language)
        return None, base_slots, _not_found()

    if slot and is_broad_area_place_query(user_query) and len(kv_places) < 2:
        known_rows = broad_area_disambig_known_places(user_query)
        if len(known_rows) >= 2:
            candidate_key = (
                "origin_candidates" if slot == "origin" else "destination_candidates"
            )
            candidates = [
                _resolved_place_from_known(row, user_query) for row in known_rows[:3]
            ]
            merged = _save_candidates(base_slots, candidate_key, candidates)
            pick_msg = PICK_PLACE[language].format(
                options=_candidate_lines(candidates, language)
            )
            return None, merged, pick_msg

    if len(kv_places) > 1 and slot:
        candidate_key = (
            "origin_candidates" if slot == "origin" else "destination_candidates"
        )
        candidates = _places_to_candidates(kv_places, user_query=user_query)
        merged = _save_candidates(base_slots, candidate_key, candidates)
        pick_msg = PICK_PLACE[language].format(
            options=_candidate_lines(candidates, language)
        )
        return None, merged, pick_msg

    place = kv_places[0]
    if not place_matches_user_query(
        user_query, place_name=place.name, formatted_address=place.formatted_address
    ):
        suggestion = suggest_place_alias(user_query)
        if suggestion:
            label = place_ui_label(user_query, canonical_name=suggestion)
            return None, base_slots, blocks_place_did_you_mean(label, language)
        return None, base_slots, _not_found()
    return _resolved_place_dict(place, user_query), base_slots, None


async def _resolve_place_slot(
    message: str,
    slots: dict[str, str],
    candidate_key: str,
    language: str,
) -> tuple[dict | None, dict[str, str], str | list[ChatBlock] | None]:
    """Returns (resolved_place_dict, updated_slots, error_message or error_blocks)."""
    from app.services.ai_route_parse_service import suggest_place_alias
    from app.services.ai_route_sentence_service import is_confirm_yes

    updated_slots = dict(slots)
    slot_kind: Literal["origin", "destination"] | None = None
    if candidate_key == "origin_candidates":
        slot_kind = "origin"
    elif candidate_key == "destination_candidates":
        slot_kind = "destination"

    suggested_query = (updated_slots.get("suggested_place_query") or "").strip()
    if suggested_query and is_confirm_yes(message):
        updated_slots = {k: v for k, v in updated_slots.items() if k != "suggested_place_query"}
        resolved, _, err = await _resolve_place_by_query(
            suggested_query, language, slot=slot_kind, slots=updated_slots
        )
        if resolved:
            return resolved, updated_slots, None
        return None, updated_slots, err

    candidates = _load_candidates(updated_slots, candidate_key)

    if candidates:
        picked = _match_named_candidate(message, candidates)
        if picked:
            return picked, {k: v for k, v in updated_slots.items() if k != candidate_key}, None
        return None, updated_slots, PLACE_PICK_RETRY[language].format(
            options=_candidate_lines(candidates, language)
        )

    user_query = (
        refine_place_query_for_slot(message, slot_kind)  # type: ignore[arg-type]
        if slot_kind
        else message.strip()
    )
    issue = classify_place_input(user_query)
    if issue != "ok":
        return None, updated_slots, blocks_to_plain_text(blocks_place_input_error(issue, language))

    from app.services.ai_route_parse_service import is_broad_area_place_query

    known = lookup_known_kv_place(user_query)
    if known is not None and not (slot_kind and is_broad_area_place_query(user_query)):
        return _resolved_place_from_known(known, user_query), updated_slots, None

    message = normalize_place_query(user_query)

    from app.services.ai_route_parse_service import (
        broad_area_disambig_known_places,
        is_broad_area_place_query,
    )

    places = await search_places_kv(message, limit=8)
    kv_places = _dedupe_kv_places([p for p in places if place_detail_in_kv(p)], limit=3)
    if places and not kv_places:
        return None, updated_slots, blocks_outside_kv(language)
    if not kv_places:
        suggestion = suggest_place_alias(user_query)
        if suggestion:
            updated_slots["suggested_place_query"] = suggestion
            label = place_ui_label(user_query, canonical_name=suggestion)
            return None, updated_slots, blocks_place_did_you_mean(label, language)
        return None, updated_slots, blocks_place_not_found(language)

    if slot_kind and is_broad_area_place_query(user_query) and len(kv_places) < 2:
        known_rows = broad_area_disambig_known_places(user_query)
        if len(known_rows) >= 2:
            candidates = [
                _resolved_place_from_known(row, user_query) for row in known_rows[:3]
            ]
            updated_slots = _save_candidates(updated_slots, candidate_key, candidates)
            return None, updated_slots, PICK_PLACE[language].format(
                options=_candidate_lines(candidates, language)
            )

    if len(kv_places) == 1:
        place = kv_places[0]
        if not place_matches_user_query(
            user_query, place_name=place.name, formatted_address=place.formatted_address
        ):
            suggestion = suggest_place_alias(user_query)
            if suggestion:
                updated_slots["suggested_place_query"] = suggestion
                label = place_ui_label(user_query, canonical_name=suggestion)
                return None, updated_slots, blocks_place_did_you_mean(label, language)
            return None, updated_slots, blocks_place_not_found(language)
        return (_resolved_place_dict(place, user_query), updated_slots, None)

    candidates = _places_to_candidates(kv_places, user_query=user_query)
    updated_slots = _save_candidates(updated_slots, candidate_key, candidates)
    return None, updated_slots, PICK_PLACE[language].format(
        options=_candidate_lines(candidates, language)
    )


async def _handle_station_flow(
    message: str, slots: dict[str, str], language: str
) -> IntentResult:
    candidates = _load_candidates(slots, "station_candidates")
    if candidates:
        picked = _match_named_candidate(message, candidates)
        if picked:
            detail = get_location_detail_by_id(picked["id"])
            if detail is None:
                return _flow_result(
                    STATION_NOT_FOUND[language],
                    flow="station_info",
                    slots={},
                )
            return _flow_result(
                blocks=blocks_for_station(detail, language),
                flow=None,
                slots={},
                actions=[
                    ChatAction(
                        type="open_station_detail",
                        station_id=picked["id"],
                        station_name=detail.name,
                    )
                ],
            )
        return _flow_result(
            blocks=blocks_pick_retry(
                STATION_PICK_RETRY[language].split("\n")[0],
                candidates,
                language,
            ),
            flow="station_info",
            slots=slots,
        )

    query = _normalize_station_query(message.strip())
    if not query or query.lower() in STATION_CHIP_MESSAGES:
        return _flow_result(
            blocks=blocks_ask_station(language),
            flow="station_info",
            slots={},
        )

    if is_unclear_place_reply(message):
        return _flow_result(
            blocks=_place_input_blocks(message, language),
            flow="station_info",
            slots={},
        )

    matches = search_station_locations(query, limit=5)
    if not matches:
        return _flow_result(
            blocks=blocks_station_not_found(language),
            flow="station_info",
            slots={},
        )

    if len(matches) > 1:
        station_candidates: list[dict[str, str]] = []
        seen_names: set[str] = set()
        for item in matches:
            name_key = item.name.strip().lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)
            station_candidates.append({"id": item.id, "name": item.name})
            if len(station_candidates) >= 3:
                break
        updated_slots = _save_candidates({}, "station_candidates", station_candidates)
        return _flow_result(
            blocks=blocks_station_pick(station_candidates, language),
            flow="station_info",
            slots=updated_slots,
        )

    station = matches[0]
    detail = get_location_detail_by_id(station.id)
    if detail is None:
        return _flow_result(
            blocks=blocks_station_not_found(language),
            flow="station_info",
            slots={},
        )

    return _flow_result(
        blocks=blocks_for_station(detail, language),
        flow=None,
        slots={},
        actions=[
            ChatAction(
                type="open_station_detail",
                station_id=station.id,
                station_name=detail.name,
            )
        ],
    )


async def _fetch_kv_overview_forecast():
    return await get_weather_forecast(
        WeatherForecastRequest(destination_name=KV_WEATHER_CITY, departure_time="now")
    )


async def _weather_for_place_query(
    query: str, language: str
) -> tuple[object | None, str | None, str | list[ChatBlock] | None]:
    """Returns (forecast, region_label, error_message). Uses weather API only — no Gemini."""
    user_query = query.strip()
    if not is_plausible_place_query(user_query):
        return None, None, WEATHER_NOT_FOUND[language]

    location = normalize_place_query(user_query)
    places = await search_places_kv(location, limit=3)
    kv_places = [p for p in places if place_detail_in_kv(p)]
    if places and not kv_places:
        return None, None, blocks_outside_kv(language)
    if not kv_places:
        return None, None, blocks_weather_not_found(language)
    place = kv_places[0]
    matched = place_matches_user_query(
        user_query, place_name=place.name, formatted_address=place.formatted_address
    )
    if not matched:
        return None, None, WEATHER_NOT_FOUND[language]

    location_name = place_ui_label(user_query, google_name=place.name, canonical_name=place.name)
    try:
        forecast = await get_weather_forecast(
            WeatherForecastRequest(
                destination_name=location_name,
                departure_time="now",
                lat=place.lat,
                lon=place.lon,
            )
        )
        return forecast, location_name, None
    except (HTTPException, Exception):
        return None, None, WEATHER_NOT_FOUND[language]


async def _handle_weather_flow(
    message: str, slots: dict[str, str], language: str
) -> IntentResult:
    updated = dict(slots)
    place_query = _extract_weather_place(message) or updated.get("weather_location", "").strip()
    msg_lower = message.lower().strip()
    is_bare = msg_lower in WEATHER_BARE_TRIGGERS or not place_query

    if not updated.get("kv_overview_shown"):
        kv_forecast = None
        try:
            kv_forecast = await _fetch_kv_overview_forecast()
        except (HTTPException, Exception):
            kv_forecast = None
        updated["kv_overview_shown"] = "1"
        overview_blocks = (
            blocks_for_kv_weather_overview(kv_forecast, language)
            if kv_forecast is not None
            else [
                ChatBlock(
                    type="callout",
                    tone="warning",
                    text={
                        "en": "Klang Valley weather is temporarily unavailable.",
                        "ms": "Cuaca Lembah Klang tidak tersedia buat sementara waktu.",
                        "zh": "巴生谷天气暂不可用。",
                    }[language],
                )
            ]
        )

        if is_bare:
            return _flow_result(
                blocks=overview_blocks + blocks_ask_weather_location(language),
                flow="weather",
                slots=updated,
            )

        forecast, region_label, local_err = await _weather_for_place_query(place_query, language)
        if local_err:
            err_blocks = (
                local_err
                if isinstance(local_err, list)
                else blocks_weather_not_found(language) + blocks_ask_weather_location(language)
            )
            return _flow_result(
                blocks=overview_blocks + err_blocks,
                flow="weather",
                slots=updated,
            )
        local_blocks = blocks_for_weather(forecast, language, region_label=region_label)
        return _flow_result(
            blocks=overview_blocks + local_blocks,
            flow=None,
            slots={},
        )

    if is_bare or is_unclear_place_reply(message):
        return _flow_result(
            blocks=blocks_ask_weather_location(language),
            flow="weather",
            slots=updated,
        )

    forecast, region_label, local_err = await _weather_for_place_query(place_query, language)
    if local_err:
        err_blocks = (
            local_err
            if isinstance(local_err, list)
            else blocks_weather_not_found(language) + blocks_ask_weather_location(language)
        )
        return _flow_result(blocks=err_blocks, flow="weather", slots=updated)
    return _flow_result(
        blocks=blocks_for_weather(forecast, language, region_label=region_label),
        flow=None,
        slots={},
    )


PLAN_BARE_TRIGGERS = {
    "i want to plan a route",
    "plan a route",
    "how do i plan a route in eldergo",
    "rancang laluan",
}


async def _finish_plan_route(
    updated: dict[str, str], departure: str, language: str
) -> IntentResult:
    origin = json.loads(updated["origin_resolved"])
    destination = json.loads(updated["destination_resolved"])

    origin_label = _route_place_label(origin)
    destination_label = _route_place_label(destination)

    departure_label = format_departure_display_label(departure, language)
    ready_blocks = blocks_route_ready(origin_label, destination_label, departure_label, language)

    return _flow_result(
        blocks=ready_blocks,
        flow=None,
        slots={},
        actions=[
            ChatAction(
                type="compute_route",
                origin_name=origin_label,
                destination_name=destination_label,
                departure_time=departure,
                origin_lat=origin.get("lat"),
                origin_lon=origin.get("lon"),
                origin_google_place_id=origin.get("google_place_id"),
                destination_lat=destination.get("lat"),
                destination_lon=destination.get("lon"),
                destination_google_place_id=destination.get("google_place_id"),
            )
        ],
    )


def _ingest_plan_route_metadata(message: str, updated: dict[str, str]) -> None:
    from app.services.ai_route_sentence_service import (
        extract_preference_hint,
        has_departure_signal,
        parse_departure_time,
    )

    pref = extract_preference_hint(message)
    if pref:
        updated["preference_hint"] = pref
    if has_departure_signal(message):
        dep = parse_departure_time(message)
        if dep:
            updated["departure_time"] = dep


def _is_metadata_only_message(message: str) -> bool:
    from app.services.ai_route_sentence_service import (
        extract_preference_hint,
        extract_route_endpoints,
        has_departure_signal,
        parse_departure_time,
    )

    origin, destination = extract_route_endpoints(message)
    if origin and destination:
        return False

    if extract_preference_hint(message):
        return True
    if has_departure_signal(message) and parse_departure_time(message):
        return True
    return False


async def _try_apply_full_route_sentence(
    message: str, updated: dict[str, str], language: str
) -> IntentResult | None:
    """Parse and resolve a full origin+destination (+ optional time) in one message."""
    from app.services.ai_route_sentence_service import (
        has_explicit_departure_or_preference,
        is_confirm_no,
        is_confirm_yes,
        parse_route_sentence,
    )

    from app.services.ai_route_sentence_service import is_plan_route_intent_message

    if is_plan_route_intent_message(message):
        return None

    parsed = parse_route_sentence(message)
    if not (parsed.origin and parsed.destination):
        return None
    if not (
        is_plausible_place_query(parsed.origin) and is_plausible_place_query(parsed.destination)
    ):
        return None

    work = dict(updated)
    origin_place, o_slots, origin_err = await _resolve_place_by_query(
        parsed.origin, language, slot="origin", slots=work
    )
    work.update(o_slots)
    if origin_err:
        return _flow_error_result(origin_err, flow="plan_route", slots=work)
    if not origin_place:
        return None

    dest_place, d_slots, dest_err = await _resolve_place_by_query(
        parsed.destination, language, slot="destination", slots=work
    )
    work.update(d_slots)
    if dest_err:
        return _flow_error_result(dest_err, flow="plan_route", slots=work)
    if not dest_place:
        return None

    updated = work
    updated["origin_resolved"] = json.dumps(origin_place)
    updated["destination_resolved"] = json.dumps(dest_place)
    if parsed.departure:
        updated["departure_time"] = parsed.departure

    if updated.get("awaiting_plan_confirm") == "1":
        if is_confirm_yes(message):
            updated.pop("awaiting_plan_confirm", None)
            dep = updated.get("departure_time") or "now"
            return await _finish_plan_route(updated, dep, language)
        if is_confirm_no(message):
            updated.pop("awaiting_plan_confirm", None)
            return _flow_result(
                blocks=blocks_ask_route_origin(language),
                flow="plan_route",
                slots={},
            )
        o_label = _route_place_label(origin_place)
        d_label = _route_place_label(dest_place)
        return _flow_result(
            blocks=blocks_ask_confirm_plan_route(o_label, d_label, language),
            flow="plan_route",
            slots=updated,
        )

    if has_explicit_departure_or_preference(message, updated):
        dep = updated.get("departure_time") or "now"
        return await _maybe_finish_with_preference(updated, dep, message, language)

    updated["awaiting_plan_confirm"] = "1"
    o_label = _route_place_label(origin_place)
    d_label = _route_place_label(dest_place)
    return _flow_result(
        blocks=blocks_ask_confirm_plan_route(o_label, d_label, language),
        flow="plan_route",
        slots=updated,
    )


async def enter_plan_route_partial(
    message: str,
    *,
    origin: str | None,
    destination: str | None,
    departure: str | None,
    language: str,
    planning_mode: str | None = None,
) -> IntentResult:
    """Start plan_route when only origin or only destination is known."""
    from app.services.ai_route_sentence_service import parse_departure_time

    slots: dict[str, str] = {}
    if planning_mode:
        slots["planning_mode"] = planning_mode
    if departure:
        slots["departure_time"] = parse_departure_time(departure) or departure

    if destination and not origin:
        place, merged, err = await _resolve_place_by_query(
            destination, language, slot="destination", slots=slots
        )
        slots.update(merged)
        if err:
            return _flow_error_result(err, flow="plan_route", slots=slots)
        if place:
            slots["destination_resolved"] = json.dumps(place)
        return _flow_result(
            blocks=blocks_ask_route_origin(language),
            flow="plan_route",
            slots=slots,
        )

    if origin and not destination:
        place, merged, err = await _resolve_place_by_query(
            origin, language, slot="origin", slots=slots
        )
        slots.update(merged)
        if err:
            return _flow_error_result(err, flow="plan_route", slots=slots)
        if place:
            slots["origin_resolved"] = json.dumps(place)
        return _flow_result(
            blocks=blocks_ask_route_destination(language),
            flow="plan_route",
            slots=slots,
        )

    if origin and destination:
        o_place, o_slots, o_err = await _resolve_place_by_query(
            origin, language, slot="origin", slots=slots
        )
        slots.update(o_slots)
        if o_err:
            return _flow_error_result(o_err, flow="plan_route", slots=slots)
        d_place, d_slots, d_err = await _resolve_place_by_query(
            destination, language, slot="destination", slots=slots
        )
        slots.update(d_slots)
        if d_err:
            return _flow_error_result(d_err, flow="plan_route", slots=slots)
        if o_place and d_place:
            slots["origin_resolved"] = json.dumps(o_place)
            slots["destination_resolved"] = json.dumps(d_place)
            dep = slots.get("departure_time") or "now"
            return await _maybe_finish_with_preference(updated=slots, departure=dep, message=message, language=language)

    return await _handle_plan_route_flow(message, slots, language)


async def _try_apply_partial_route_sentence(
    message: str, updated: dict[str, str], language: str
) -> IntentResult | None:
    """Fill one endpoint from a single-place or Gemini-assisted utterance."""
    from app.services.ai_intent_gemini_service import try_gemini_travel_slots
    from app.services.ai_route_sentence_service import parse_route_sentence, parse_departure_time

    parsed = parse_route_sentence(message)
    origin_q, dest_q = parsed.origin, parsed.destination

    if not origin_q and not dest_q:
        travel = await try_gemini_travel_slots(message)
        if travel:
            origin_q, dest_q = travel.origin, travel.destination
            if travel.departure and not updated.get("departure_time"):
                updated["departure_time"] = (
                    parse_departure_time(travel.departure) or travel.departure
                )
            if travel.preference:
                updated["preference_hint"] = travel.preference

    if parsed.departure and not updated.get("departure_time"):
        updated["departure_time"] = parsed.departure

    if dest_q and not origin_q and not updated.get("destination_resolved"):
        if updated.get("origin_resolved"):
            return None
        place, merged, err = await _resolve_place_by_query(
            dest_q, language, slot="destination", slots=updated
        )
        updated.update(merged)
        if err:
            return _flow_error_result(err, flow="plan_route", slots=updated)
        if not place:
            return None
        updated["destination_resolved"] = json.dumps(place)
        if updated.get("origin_resolved"):
            dep = updated.get("departure_time") or "now"
            return await _maybe_finish_with_preference(updated, dep, message, language)
        return _flow_result(
            blocks=blocks_ask_route_origin(language),
            flow="plan_route",
            slots=updated,
        )

    if origin_q and not dest_q:
        if updated.get("destination_resolved"):
            return None
        if updated.get("origin_resolved"):
            return None
        place, merged, err = await _resolve_place_by_query(
            origin_q, language, slot="origin", slots=updated
        )
        updated.update(merged)
        if err:
            return _flow_error_result(err, flow="plan_route", slots=updated)
        if not place:
            return None
        updated["origin_resolved"] = json.dumps(place)
        if updated.get("destination_resolved"):
            dep = updated.get("departure_time") or "now"
            return await _maybe_finish_with_preference(updated, dep, message, language)
        return _flow_result(
            blocks=blocks_ask_route_destination(language),
            flow="plan_route",
            slots=updated,
        )

    return None


async def _handle_recommendation_plan_route(
    message: str, updated: dict[str, str], language: str
) -> IntentResult:
    """Collect origin, destination, then time/preferences for route recommendation requests."""
    _ingest_plan_route_metadata(message, updated)

    partial = await _try_apply_partial_route_sentence(message, updated, language)
    if partial is not None:
        return partial

    full = await _try_apply_full_route_sentence(message, updated, language)
    if full is not None:
        return full

    if not updated.get("origin_resolved"):
        return _flow_result(blocks=blocks_ask_route_origin(language), flow="plan_route", slots=updated)
    if not updated.get("destination_resolved"):
        return _flow_result(
            blocks=blocks_ask_route_destination(language),
            flow="plan_route",
            slots=updated,
        )
    departure = updated.get("departure_time") or _parse_departure_time(message)
    return await _maybe_finish_with_preference(updated, departure or "now", message, language)


async def _maybe_finish_with_preference(
    updated: dict[str, str],
    departure: str,
    message: str,
    language: str,
) -> IntentResult:
    from app.services.ai_route_sentence_service import (
        has_explicit_departure_or_preference,
        is_confirm_no,
        is_confirm_yes,
        is_preferences_done_reply,
        parse_departure_time,
    )

    if updated.get("awaiting_preferences_setup") == "1":
        if is_preferences_done_reply(message):
            updated.pop("awaiting_preferences_setup", None)
            final_dep = updated.get("departure_time") or departure or "now"
            return await _finish_plan_route(updated, final_dep, language)
        return _flow_result(
            blocks=blocks_ask_preferences_before_route(language),
            flow="plan_route",
            slots=updated,
            actions=[ChatAction(type="open_preference")],
        )

    if updated.get("awaiting_defaults_confirm") == "1":
        from app.services.ai_route_sentence_service import extract_preference_hint

        if is_confirm_yes(message):
            updated.pop("awaiting_defaults_confirm", None)
            final_dep = updated.get("departure_time") or departure or "now"
            return await _finish_plan_route(updated, final_dep, language)
        if is_confirm_no(message):
            updated.pop("awaiting_defaults_confirm", None)
            updated["awaiting_preferences_setup"] = "1"
            return _flow_result(
                blocks=blocks_ask_preferences_before_route(language),
                flow="plan_route",
                slots=updated,
                actions=[ChatAction(type="open_preference")],
            )
        dep = parse_departure_time(message)
        pref = extract_preference_hint(message)
        if dep or pref:
            updated.pop("awaiting_defaults_confirm", None)
            if dep:
                updated["departure_time"] = dep
            if pref:
                updated["preference_hint"] = pref
            final_dep = updated.get("departure_time") or departure or "now"
            return await _finish_plan_route(updated, final_dep, language)
        return _flow_result(
            blocks=blocks_ask_use_defaults(language),
            flow="plan_route",
            slots=updated,
        )

    explicit = has_explicit_departure_or_preference(message, updated)
    final_dep = updated.get("departure_time") or (
        parse_departure_time(message) if explicit else None
    ) or departure

    if not explicit:
        updated["awaiting_defaults_confirm"] = "1"
        return _flow_result(
            blocks=blocks_ask_use_defaults(language),
            flow="plan_route",
            slots=updated,
        )

    final_dep = final_dep or "now"
    from app.services.ai_route_sentence_service import validate_departure_iso
    from app.services.departure_time_service import normalize_departure_key

    preset_keys = frozenset({"now", "morning_peak", "midday", "evening_peak", "night"})
    dep_key = normalize_departure_key(final_dep)
    if dep_key not in preset_keys:
        status = validate_departure_iso(final_dep, message=message)
        if status == "past" and updated.get("awaiting_departure_clarify") != "1":
            updated["awaiting_departure_clarify"] = "1"
            from app.services.chat_blocks_service import blocks_departure_time_past

            return _flow_result(
                blocks=blocks_departure_time_past(language),
                flow="plan_route",
                slots=updated,
            )
        if status == "needs_date":
            return _flow_result(
                blocks=blocks_ask_departure_time(language),
                flow="plan_route",
                slots=updated,
            )
    updated.pop("awaiting_departure_clarify", None)
    updated["departure_time"] = final_dep
    return await _finish_plan_route(updated, final_dep, language)


async def _handle_plan_route_flow(
    message: str, slots: dict[str, str], language: str
) -> IntentResult:
    from app.services.ai_intent_gemini_service import is_route_recommendation_message

    updated = dict(slots)
    msg_lower = message.lower().strip()
    _ingest_plan_route_metadata(message, updated)

    if updated.get("awaiting_departure_clarify") == "1":
        dep = updated.get("departure_time") or _parse_departure_time(message)
        if dep:
            updated.pop("awaiting_departure_clarify", None)
            if updated.get("origin_resolved") and updated.get("destination_resolved"):
                return await _maybe_finish_with_preference(updated, dep, message, language)

    if is_route_recommendation_message(message) or updated.get("planning_mode") == "recommendation":
        updated["planning_mode"] = "recommendation"
        return await _handle_recommendation_plan_route(message, updated, language)

    if updated.get("awaiting_plan_confirm") == "1":
        from app.services.ai_route_sentence_service import is_confirm_no, is_confirm_yes

        if is_confirm_yes(message):
            updated.pop("awaiting_plan_confirm", None)
            dep = updated.get("departure_time") or "now"
            return await _finish_plan_route(updated, dep, language)
        if is_confirm_no(message):
            updated.pop("awaiting_plan_confirm", None)
            return _flow_result(
                blocks=blocks_ask_route_origin(language),
                flow="plan_route",
                slots={},
            )
        origin = json.loads(updated["origin_resolved"]) if updated.get("origin_resolved") else None
        dest = json.loads(updated["destination_resolved"]) if updated.get("destination_resolved") else None
        if origin and dest:
            return _flow_result(
                blocks=blocks_ask_confirm_plan_route(
                    _route_place_label(origin), _route_place_label(dest), language
                ),
                flow="plan_route",
                slots=updated,
            )

    if updated.get("origin_resolved") and updated.get("destination_resolved"):
        departure = updated.get("departure_time") or _parse_departure_time(message)
        return await _maybe_finish_with_preference(
            updated, departure or "now", message, language
        )

    if not updated.get("origin_resolved") and (
        msg_lower in PLAN_BARE_TRIGGERS
        or (not updated and _is_plan_route_starter(message) and len(msg_lower) < 60)
    ):
        return _flow_result(blocks=blocks_ask_route_origin(language), flow="plan_route", slots={})

    partial_route = await _try_apply_partial_route_sentence(message, updated, language)
    if partial_route is not None:
        return partial_route

    full_route = await _try_apply_full_route_sentence(message, updated, language)
    if full_route is not None:
        return full_route

    if _is_metadata_only_message(message):
        if not updated.get("origin_resolved"):
            return _flow_result(blocks=blocks_ask_route_origin(language), flow="plan_route", slots=updated)
        if not updated.get("destination_resolved"):
            return _flow_result(
                blocks=blocks_ask_route_destination(language),
                flow="plan_route",
                slots=updated,
            )
        departure = updated.get("departure_time") or _parse_departure_time(message)
        if departure:
            return await _maybe_finish_with_preference(updated, departure, message, language)
        return _flow_result(blocks=blocks_ask_departure_time(language), flow="plan_route", slots=updated)

    if not updated.get("origin_resolved"):
        picked, updated = _try_pick_candidate_from_slots(message, updated, "origin_candidates")
        if picked:
            updated["origin_resolved"] = json.dumps(picked)
            if updated.get("destination_resolved"):
                departure = updated.get("departure_time") or _parse_departure_time(message)
                return await _maybe_finish_with_preference(
                    updated, departure or "now", message, language
                )
            return _flow_result(
                blocks=blocks_ask_route_destination(language),
                flow="plan_route",
                slots=updated,
            )

    if updated.get("origin_resolved") and not updated.get("destination_resolved"):
        picked, updated = _try_pick_candidate_from_slots(message, updated, "destination_candidates")
        if picked:
            updated["destination_resolved"] = json.dumps(picked)
            return await _maybe_finish_with_preference(updated, "now", message, language)

    if not updated.get("origin_resolved") and not updated.get("destination_resolved"):
        from app.services.ai_exploratory_poi_service import is_enroute_rest_exploratory

        if is_enroute_rest_exploratory(message):
            return None

        from app.services.ai_route_sentence_service import parse_route_sentence

        parsed = parse_route_sentence(message)
        rule_origin, rule_dest = parsed.origin, parsed.destination
        gemini_origin, gemini_dest = rule_origin, rule_dest
        if not (rule_origin and rule_dest):
            origin_hint = None
            dest_hint = None
            if updated.get("origin_resolved"):
                origin_hint = _route_place_label(json.loads(updated["origin_resolved"]))
            if updated.get("destination_resolved"):
                dest_hint = _route_place_label(json.loads(updated["destination_resolved"]))
            gemini_origin, gemini_dest = await try_gemini_route_pair(
                message, origin_hint=origin_hint, destination_hint=dest_hint
            )
        origin_q = gemini_origin or rule_origin
        dest_q = gemini_dest or rule_dest
        if origin_q and dest_q:
            work = dict(updated)
            origin_place, o_slots, origin_err = await _resolve_place_by_query(
                origin_q, language, slot="origin", slots=work
            )
            work.update(o_slots)
            if origin_err:
                return _flow_error_result(origin_err, flow="plan_route", slots=work)
            dest_place, d_slots, dest_err = await _resolve_place_by_query(
                dest_q, language, slot="destination", slots=work
            )
            work.update(d_slots)
            if dest_err:
                return _flow_error_result(dest_err, flow="plan_route", slots=work)
            if origin_place and dest_place:
                updated = work
                updated["origin_resolved"] = json.dumps(origin_place)
                updated["destination_resolved"] = json.dumps(dest_place)
                departure = (
                    parsed.departure
                    or updated.get("departure_time")
                    or _parse_departure_time(message)
                )
                return await _maybe_finish_with_preference(
                    updated, departure or "now", message, language
                )

    if is_unclear_place_reply(message):
        if not updated.get("origin_resolved"):
            if _load_candidates(updated, "origin_candidates"):
                return _flow_result(
                    PLACE_PICK_RETRY[language].format(
                        options=_candidate_lines(_load_candidates(updated, "origin_candidates"), language)
                    ),
                    flow="plan_route",
                    slots=updated,
                )
            return _flow_result(
                blocks=_place_input_blocks(message, language, slot="origin"),
                flow="plan_route",
                slots=updated,
            )
        if not updated.get("destination_resolved"):
            if _load_candidates(updated, "destination_candidates"):
                return _flow_result(
                    PLACE_PICK_RETRY[language].format(
                        options=_candidate_lines(
                            _load_candidates(updated, "destination_candidates"), language
                        )
                    ),
                    flow="plan_route",
                    slots=updated,
                )
            return _flow_result(
                blocks=_place_input_blocks(message, language, slot="destination"),
                flow="plan_route",
                slots=updated,
            )
        if _departure_input_is_invalid(message):
            return _flow_result(blocks=blocks_invalid_departure(language), flow="plan_route", slots=updated)
        return _flow_result(blocks=blocks_ask_departure_time(language), flow="plan_route", slots=updated)

    if not updated.get("origin_resolved"):
        if updated.get("origin_pending"):
            resolved, updated, error = await _resolve_place_slot(
                message, updated, "origin_candidates", language
            )
            if error:
                return _flow_error_result(error, flow="plan_route", slots=updated)
            if resolved is None and error is None:
                return _flow_result(
                    blocks=_place_input_blocks(message, language, slot="origin"),
                    flow="plan_route",
                    slots=updated,
                )
            if resolved is None:
                return _flow_error_result(
                    error or blocks_place_not_found(language),
                    flow="plan_route",
                    slots={k: v for k, v in updated.items() if not k.startswith("origin_")},
                )
            updated["origin_resolved"] = json.dumps(resolved)
            updated.pop("origin_pending", None)
        else:
            resolved, updated, error = await _resolve_place_slot(
                message, updated, "origin_candidates", language
            )
            if error:
                updated["origin_pending"] = "1"
                return _flow_error_result(error, flow="plan_route", slots=updated)
            if resolved is None and error is None:
                return _flow_result(
                    blocks=_place_input_blocks(message, language, slot="origin"),
                    flow="plan_route",
                    slots=updated,
                )
            if resolved is None:
                return _flow_error_result(
                    error or blocks_place_not_found(language),
                    flow="plan_route",
                    slots={},
                )
            updated["origin_resolved"] = json.dumps(resolved)
            if updated.get("destination_resolved"):
                departure = updated.get("departure_time") or _parse_departure_time(message)
                return await _maybe_finish_with_preference(
                    updated, departure or "now", message, language
                )
            return _flow_result(
                blocks=blocks_ask_route_destination(language),
                flow="plan_route",
                slots=updated,
            )

    if not updated.get("destination_resolved"):
        if updated.get("destination_pending"):
            resolved, updated, error = await _resolve_place_slot(
                message, updated, "destination_candidates", language
            )
            if error:
                return _flow_error_result(error, flow="plan_route", slots=updated)
            if resolved is None and error is None:
                return _flow_result(
                    blocks=_place_input_blocks(message, language, slot="destination"),
                    flow="plan_route",
                    slots=updated,
                )
            if resolved is None:
                return _flow_error_result(
                    error or blocks_place_not_found(language),
                    flow="plan_route",
                    slots={k: v for k, v in updated.items() if not k.startswith("destination_")},
                )
            updated["destination_resolved"] = json.dumps(resolved)
            updated.pop("destination_pending", None)
        else:
            resolved, updated, error = await _resolve_place_slot(
                message, updated, "destination_candidates", language
            )
            if error:
                updated["destination_pending"] = "1"
                return _flow_error_result(error, flow="plan_route", slots=updated)
            if resolved is None and error is None:
                return _flow_result(
                    blocks=_place_input_blocks(message, language, slot="destination"),
                    flow="plan_route",
                    slots=updated,
                )
            if resolved is None:
                return _flow_error_result(
                    error or blocks_place_not_found(language),
                    flow="plan_route",
                    slots={"origin_resolved": updated["origin_resolved"]},
                )
            updated["destination_resolved"] = json.dumps(resolved)
            return await _maybe_finish_with_preference(updated, "now", message, language)

    if _departure_input_is_invalid(message):
        return _flow_result(blocks=blocks_invalid_departure(language), flow="plan_route", slots=updated)

    departure = updated.get("departure_time") or _parse_departure_time(message)
    return await _maybe_finish_with_preference(updated, departure or "now", message, language)


async def resolve_chat_flow(message: str, request: AIMessageRequest) -> IntentResult | None:
    from app.services.ai_language import resolve_response_language

    language = resolve_response_language(request, message)
    flow: FlowType | None = request.chat_flow  # type: ignore[assignment]
    slots = dict(request.flow_slots or {})
    explicit_flow = _explicit_flow_for_message(message)

    if explicit_flow is not None and (explicit_flow != flow or _is_bare_flow_chip(message)):
        flow = explicit_flow
        slots = {}
    elif flow is None:
        if explicit_flow:
            flow = explicit_flow
            slots = {}
        else:
            from app.services.ai_exploratory_poi_service import is_enroute_rest_exploratory
            from app.services.ai_intent_gemini_service import is_route_recommendation_message

            rule_origin, rule_dest = try_rule_route_pair(message)
            if rule_origin and rule_dest and not is_enroute_rest_exploratory(message):
                flow = "plan_route"
                slots = {}
            elif (rule_origin or rule_dest) and not is_enroute_rest_exploratory(message):
                from app.services.ai_route_parse_service import has_single_route_endpoint

                if (
                    has_single_route_endpoint(message)
                    or _explicit_flow_for_message(message) == "plan_route"
                    or _is_plan_route_starter(message)
                    or is_route_recommendation_message(message)
                    or re.search(
                        r"\b(?:go\s+to|wanna|want\s+to|heading\s+to|get\s+to)\b",
                        message,
                        re.I,
                    )
                ):
                    flow = "plan_route"
                    slots = {}
            elif is_route_recommendation_message(message):
                flow = "plan_route"
                slots = {"planning_mode": "recommendation"}
            elif _is_plan_route_starter(message):
                flow = "plan_route"
                slots = {}
            elif _is_station_starter(message):
                flow = "station_info"
            elif _is_weather_starter(message) or _matches_any(message, WEATHER_PATTERNS):
                flow = "weather"
                if not _starter_has_place(message):
                    slots = {}
            elif _looks_like_station_query(message):
                flow = "station_info"

    if flow == "station_info":
        return await _handle_station_flow(message, slots, language)
    if flow == "weather":
        return await _handle_weather_flow(message, slots, language)
    if flow == "plan_route":
        return await _handle_plan_route_flow(message, slots, language)

    return None
