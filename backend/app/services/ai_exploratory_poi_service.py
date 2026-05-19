"""Exploratory POI queries — cafes/rest stops via Places; senior-common POI defers to Gemini."""

from __future__ import annotations

import re

from app.schemas.ai import ChatAction, ChatBlock
from app.services.ai_intent_service import IntentResult
from app.services.ai_route_parse_service import (
    is_plausible_place_query,
    normalize_place_query,
    place_matches_user_query,
    place_ui_label,
)
from app.services.chat_blocks_service import blocks_exploratory_places, blocks_to_plain_text
from app.services.klang_valley_service import place_detail_in_kv
from app.services.places_service import search_places_kv

ENROUTE_MARKERS = (
    re.compile(r"中途"),
    re.compile(r"\balong the way\b", re.I),
    re.compile(r"\bmidway\b", re.I),
    re.compile(r"\bbetween\b.*\band\b", re.I),
)

EXPLORATORY_POI_PATTERNS = (
    re.compile(
        r"\b(?:near(?:by)?|around|close to|berhampiran|dekat|near me)\b",
        re.I,
    ),
    re.compile(r"附近|周边|靠近"),
    re.compile(
        r"\b(?:cafe|coffee|restaurant|food|toilet|rest stop|break|shade|shelter)\b",
        re.I,
    ),
    re.compile(r"咖啡馆|餐厅|休息|厕所"),
    re.compile(
        r"\b(?:wheelchair|accessible)\s+(?:cafe|restaurant|place|spot)\b",
        re.I,
    ),
    re.compile(r"无障碍.*(?:店|餐厅|咖啡)"),
)

QUERY_STRIP_PATTERNS = (
    re.compile(
        r"^(?:where|what|which|are there|is there|find|show|list|got|got any|any)\s+",
        re.I,
    ),
    re.compile(r"^(?:附近有|有没有|哪里有)\s*"),
    re.compile(r"\s+(?:near me|nearby|in klang valley|in kl)\s*$", re.I),
    re.compile(r"\s+for\s+a\s+rest\s+stop\s*$", re.I),
    re.compile(r"\s+with\s+shade\b", re.I),
    re.compile(r"有没有"),
    re.compile(r"[、，,]\s*步行少[^、，,]*"),
    re.compile(r"[、，,]\s*遮阳[^、，,]*"),
)

ZH_CATEGORY_TO_SEARCH: dict[str, str] = {
    "咖啡馆": "cafe",
    "咖啡厅": "cafe",
    "咖啡": "cafe",
    "餐厅": "restaurant",
    "休息": "rest stop",
    "厕所": "toilet",
    "医院": "hospital",
    "诊所": "clinic",
    "药房": "pharmacy",
    "商场": "shopping mall",
    "超市": "supermarket",
    "市场": "market",
}

# Hospitals, malls, clinics, etc. — Gemini (+ Maps) gives clearer recommendations than raw Places.
SENIOR_COMMON_POI_PATTERNS = (
    re.compile(
        r"\b(?:hospitals?|clinics?|polyclinics?|medical\s+cent(?:er|re)s?|pharmacies|"
        r"malls?|shopping\s+cent(?:er|re)s?|supermarkets?|markets?|banks?|post\s+offices?)\b",
        re.I,
    ),
    re.compile(r"医院|诊所|药房|商场|超市|市场|银行|邮局"),
)

EN_CATEGORY_TO_SEARCH: dict[str, str] = {
    "hospital": "hospital",
    "hospitals": "hospital",
    "clinic": "clinic",
    "clinics": "clinic",
    "polyclinic": "clinic",
    "pharmacy": "pharmacy",
    "pharmacies": "pharmacy",
    "mall": "shopping mall",
    "malls": "shopping mall",
    "supermarket": "supermarket",
    "supermarkets": "supermarket",
    "market": "market",
    "markets": "market",
    "cafe": "cafe",
    "cafes": "cafe",
    "coffee": "cafe",
    "restaurant": "restaurant",
    "restaurants": "restaurant",
    "food": "restaurant",
    "school": "school",
    "schools": "school",
    "supermarket": "supermarket",
    "toilet": "toilet",
    "rest stop": "rest stop",
}


def is_enroute_rest_exploratory(message: str) -> bool:
    """Route corridor question (A to B) asking for stops/rest — not a new route plan."""
    text = message.strip()
    if not any(p.search(text) for p in ENROUTE_MARKERS):
        return False
    return parse_enroute_endpoints(text) is not None and (
        bool(_zh_category_search_term(text))
        or re.search(r"\b(?:rest|stop|break|cafe|coffee|food|toilet|shade)\b", text, re.I)
        or re.search(r"休息|咖啡馆|咖啡|餐厅", text)
    )


def parse_enroute_endpoints(message: str) -> tuple[str, str] | None:
    """Extract origin/destination without swallowing 中途… as part of the destination."""
    text = message.strip()
    zh = re.search(r"从\s*(.+?)\s*到\s*([^中途?，。、]+?)(?:\s*中途|\?|$|，|。)", text)
    if zh:
        origin, dest = zh.group(1).strip(), zh.group(2).strip()
        if origin and dest:
            return origin, dest
    en = re.search(
        r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\s+(?:midway|along the way|between)|\?|$|,|\.)",
        text,
        re.I,
    )
    if en:
        origin, dest = en.group(1).strip(), en.group(2).strip()
        if origin and dest:
            return origin, dest
    return None


def build_enroute_places_search(message: str, origin: str, destination: str) -> str:
    category = _zh_category_search_term(message) or "rest stop"
    origin_q = normalize_place_query(origin)
    dest_q = normalize_place_query(destination)
    for candidate in (
        f"{category} between {origin_q} and {dest_q}",
        f"{category} near {dest_q}",
        f"{category} near {origin_q}",
    ):
        if is_plausible_place_query(candidate):
            return candidate
    return ""


def is_senior_common_poi_message(message: str) -> bool:
    """Places seniors often need recommendations for (hospital, mall, clinic, pharmacy, etc.)."""
    return any(p.search(message) for p in SENIOR_COMMON_POI_PATTERNS)


def should_prefer_gemini_recommendation(message: str) -> bool:
    """Skip Places list cards; let Gemini (optionally Maps) name real venues."""
    return is_senior_common_poi_message(message)


def _en_category_search_term(message: str) -> str | None:
    lowered = message.lower()
    for label, term in sorted(EN_CATEGORY_TO_SEARCH.items(), key=lambda item: -len(item[0])):
        if re.search(rf"\b{re.escape(label)}\b", lowered):
            return term
    return None


def extract_poi_category_term(message: str) -> str | None:
    return _zh_category_search_term(message) or _en_category_search_term(message)


def is_area_poi_query(message: str) -> bool:
    """Short category + area queries, e.g. 'clinic in sunway area'."""
    text = message.strip()
    if not extract_poi_category_term(text):
        return False
    if re.search(r"\b(?:in|near|around|close to|berhampiran|dekat)\s+", text, re.I):
        return True
    if re.search(r"\barea\b", text, re.I):
        return True
    if re.search(r"附近|周边|一带|地区", text):
        return True
    return False


def is_exploratory_poi_message(message: str) -> bool:
    """Detect open-ended place exploration (not station/weather/route flows)."""
    text = message.strip()
    if not text or len(text) < 4:
        return False
    if is_senior_common_poi_message(text):
        return True
    if is_area_poi_query(text):
        return True
    if extract_poi_category_term(text) and len(text) >= 8:
        return True
    if len(text) < 12:
        return False
    if any(p.search(text) for p in EXPLORATORY_POI_PATTERNS):
        return True
    return False


def extract_poi_search_query(message: str) -> str:
    cleaned = message.strip()
    for pattern in QUERY_STRIP_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"([a-z])(near)\b", r"\1 near", cleaned, flags=re.I)
    return cleaned or message.strip()


def _zh_category_search_term(message: str) -> str | None:
    for label, term in ZH_CATEGORY_TO_SEARCH.items():
        if label in message:
            return term
    return None


def _anchor_near_zh(message: str) -> str | None:
    """Extract place anchor before 附近, e.g. KLCC 附近 -> KLCC."""
    match = re.search(r"([A-Za-z0-9]{2,24}|[\u4e00-\u9fff]{2,16})\s*附近", message)
    if not match:
        return None
    return match.group(1).strip().rstrip("?.，,、 ")


def build_places_search_query(message: str) -> str:
    """Build a short Google Places query (fits plausibility length limits)."""
    from app.services.ai_route_parse_service import _ROUTE_QUESTION_HINT

    raw = extract_poi_search_query(message)
    if is_plausible_place_query(raw) and not _ROUTE_QUESTION_HINT.search(raw):
        return normalize_place_query(raw)

    zh_anchor = _anchor_near_zh(message)
    zh_category = _zh_category_search_term(message)
    if zh_anchor:
        anchor = normalize_place_query(zh_anchor) if zh_anchor.isascii() else zh_anchor
        if zh_category:
            candidate = f"{zh_category} near {anchor}"
        else:
            candidate = f"places near {anchor}"
        if is_plausible_place_query(candidate):
            return candidate
        if is_plausible_place_query(anchor):
            return anchor

    in_area_match = re.search(
        r"\bin\s+([A-Za-z0-9][A-Za-z0-9\s.'-]{1,36})\s+area\b",
        raw,
        re.I,
    )
    category_term = extract_poi_category_term(raw)
    if in_area_match:
        anchor = in_area_match.group(1).strip().rstrip("?.,")
        if category_term:
            candidate = f"{category_term} in {anchor}"
        else:
            candidate = f"places in {anchor}"
        if is_plausible_place_query(candidate):
            return normalize_place_query(candidate)

    area_suffix = re.search(
        r"\b([A-Za-z0-9][A-Za-z0-9\s.'-]{1,36})\s+area\b",
        raw,
        re.I,
    )
    if area_suffix and category_term:
        anchor = area_suffix.group(1).strip().rstrip("?.,")
        candidate = f"{category_term} in {anchor}"
        if is_plausible_place_query(candidate):
            return normalize_place_query(candidate)

    near_match = re.search(
        r"\b(?:near|around|close to|berhampiran|dekat|in)\s+([A-Za-z0-9][A-Za-z0-9\s.'-]{1,36})",
        raw,
        re.I,
    )
    if near_match:
        anchor = near_match.group(1).strip().rstrip("?.,")
        if category_term:
            candidate = f"{category_term} near {anchor}"
        else:
            candidate = f"places near {anchor}"
        if is_plausible_place_query(candidate):
            return normalize_place_query(candidate)
        if is_plausible_place_query(anchor):
            return normalize_place_query(anchor)

    trimmed = raw[:48].strip()
    if is_plausible_place_query(trimmed):
        return normalize_place_query(trimmed)
    return ""


async def resolve_enroute_rest_poi(message: str, language: str) -> IntentResult | None:
    """Places to rest between two endpoints — do not start plan_route flow."""
    if not is_enroute_rest_exploratory(message):
        return None

    endpoints = parse_enroute_endpoints(message)
    if not endpoints:
        return None
    origin, destination = endpoints
    search_query = build_enroute_places_search(message, origin, destination)
    if not search_query:
        return None

    raw_query = extract_poi_search_query(message)
    places = await search_places_kv(search_query, limit=5)
    kv_places = [p for p in places if place_detail_in_kv(p)]
    if not kv_places:
        return None

    skip_words = {"near", "around", "between", "and", "rest", "stop", "cafe", "cafes", "places"}
    anchor_tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]{3,}", search_query)
        if token.lower() not in skip_words
    ]

    candidates: list[dict] = []
    for place in kv_places[:3]:
        if anchor_tokens:
            haystack = " ".join(
                part for part in (place.name or "", place.formatted_address or place.display_name or "") if part
            ).lower()
            if not any(token in haystack for token in anchor_tokens):
                continue
        label = place_ui_label(raw_query, google_name=place.name, canonical_name=place.name)
        candidates.append(
            {
                "label": label,
                "name": label,
                "address": (place.formatted_address or place.display_name or "").strip(),
            }
        )

    if not candidates:
        return None

    route_label = {
        "en": f"Between {place_ui_label(origin, canonical_name=origin)} and {place_ui_label(destination, canonical_name=destination)}",
        "ms": f"Antara {place_ui_label(origin, canonical_name=origin)} dan {place_ui_label(destination, canonical_name=destination)}",
        "zh": f"{place_ui_label(origin, canonical_name=origin)} 到 {place_ui_label(destination, canonical_name=destination)} 沿途",
    }[language]
    blocks = blocks_exploratory_places(candidates, language, search_label=route_label)
    return IntentResult(
        intent="enroute_rest_poi",
        answer=blocks_to_plain_text(blocks),
        answer_blocks=blocks,
        actions=[ChatAction(type="open_planning")],
        in_scope=True,
        response_source="api",
    )


async def resolve_exploratory_poi(message: str, language: str) -> IntentResult | None:
    from app.services.ai_route_parse_service import message_has_plan_route_endpoints

    if message_has_plan_route_endpoints(message):
        return None

    enroute = await resolve_enroute_rest_poi(message, language)
    if enroute is not None:
        return enroute

    if should_prefer_gemini_recommendation(message) and not is_area_poi_query(message):
        return None

    if not is_exploratory_poi_message(message):
        return None

    raw_query = extract_poi_search_query(message)
    search_query = build_places_search_query(message)
    if not search_query:
        return None
    places = await search_places_kv(search_query, limit=5)
    kv_places = [p for p in places if place_detail_in_kv(p)]
    if not kv_places:
        return None

    skip_words = {"near", "around", "cafe", "cafes", "coffee", "restaurant", "food", "places", "place"}
    anchor_tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]{3,}", search_query)
        if token.lower() not in skip_words
    ]

    candidates: list[dict] = []
    for place in kv_places[:3]:
        if anchor_tokens:
            haystack = " ".join(
                part for part in (place.name or "", place.formatted_address or place.display_name or "") if part
            ).lower()
            if not any(token in haystack for token in anchor_tokens):
                continue
        elif not place_matches_user_query(
            search_query,
            place_name=place.name,
            formatted_address=place.formatted_address,
        ):
            continue
        label = place_ui_label(raw_query, google_name=place.name, canonical_name=place.name)
        candidates.append(
            {
                "label": label,
                "name": label,
                "address": (place.formatted_address or place.display_name or "").strip(),
            }
        )

    if not candidates:
        return None

    blocks = blocks_exploratory_places(candidates, language, search_label=raw_query)
    return IntentResult(
        intent="exploratory_poi",
        answer=blocks_to_plain_text(blocks),
        answer_blocks=blocks,
        actions=[ChatAction(type="open_planning")],
        in_scope=True,
        response_source="api",
    )
