"""Route place parsing: rules + optional Gemini supplement for colloquial names."""

from __future__ import annotations

import json
import re
from typing import Literal

from app.core.config import get_settings
from app.services.ai_intent_service import extract_route_endpoints

PlaceInputIssue = Literal["ok", "empty", "too_short", "too_long", "route_sentence", "implausible"]
PlaceSlotKind = Literal["origin", "destination"]

_ROUTE_QUESTION_HINT = re.compile(
    r"\b(?:from|to|go\s+from|want\s+to|could\s+you|please|recommend|plan\s+a\s+route)\b|从\s*.+\s*到",
    re.I,
)

settings = get_settings()

PLACE_ALIASES: dict[str, str] = {
    "klcc": "Kuala Lumpur City Centre",
    "kl sentral": "Kuala Lumpur Sentral",
    "sentral": "Kuala Lumpur Sentral",
    "monash": "Monash University Malaysia",
    "monash uni": "Monash University Malaysia",
    "monash university": "Monash University Malaysia",
    "sunway": "Sunway City",
    "subang jaya": "Subang Jaya",
    "pj": "Petaling Jaya",
    "kl": "Kuala Lumpur",
    "klia": "Kuala Lumpur International Airport",
    "kl airport": "Kuala Lumpur International Airport",
    "kuala lumpur airport": "Kuala Lumpur International Airport",
    "kuala lumpur airport 1": "Kuala Lumpur International Airport Terminal 1",
    "klia terminal 1": "Kuala Lumpur International Airport Terminal 1",
    "airport 1": "Kuala Lumpur International Airport Terminal 1",
}

# Hot-path KV landmarks — skip Google Places round-trip when query matches.
KNOWN_KV_PLACES: dict[str, dict[str, object]] = {
    "monash university malaysia": {
        "name": "Monash University Malaysia",
        "label": "Monash University Malaysia",
        "lat": 3.0636,
        "lon": 101.6067,
        "google_place_id": "eldergo:place:monash",
        "formatted_address": "Monash University Malaysia, Subang Jaya, Selangor",
    },
    "kuala lumpur city centre": {
        "name": "Kuala Lumpur City Centre",
        "label": "KLCC",
        "lat": 3.1570,
        "lon": 101.7118,
        "google_place_id": "eldergo:place:klcc",
        "formatted_address": "Kuala Lumpur City Centre, Kuala Lumpur",
    },
    "kuala lumpur sentral": {
        "name": "Kuala Lumpur Sentral",
        "label": "KL Sentral",
        "lat": 3.1343,
        "lon": 101.6869,
        "google_place_id": "eldergo:place:kl-sentral",
        "formatted_address": "Kuala Lumpur Sentral, Kuala Lumpur",
    },
    "sunway city": {
        "name": "Sunway City",
        "label": "Sunway City",
        "lat": 3.0733,
        "lon": 101.6065,
        "google_place_id": "eldergo:place:sunway",
        "formatted_address": "Sunway City, Petaling Jaya, Selangor",
    },
    "subang jaya": {
        "name": "Subang Jaya",
        "label": "Subang Jaya",
        "lat": 3.0498,
        "lon": 101.5859,
        "google_place_id": "eldergo:place:subang-jaya",
        "formatted_address": "Subang Jaya, Selangor",
    },
    "petaling jaya": {
        "name": "Petaling Jaya",
        "label": "Petaling Jaya",
        "lat": 3.1073,
        "lon": 101.6065,
        "google_place_id": "eldergo:place:petaling-jaya",
        "formatted_address": "Petaling Jaya, Selangor",
    },
    "kuala lumpur": {
        "name": "Kuala Lumpur",
        "label": "Kuala Lumpur",
        "lat": 3.1390,
        "lon": 101.6869,
        "google_place_id": "eldergo:place:kl",
        "formatted_address": "Kuala Lumpur, Malaysia",
    },
    "kuala lumpur international airport": {
        "name": "Kuala Lumpur International Airport",
        "label": "KLIA",
        "lat": 2.7456,
        "lon": 101.7099,
        "google_place_id": "eldergo:place:klia",
        "formatted_address": "Kuala Lumpur International Airport, Selangor",
    },
    "kuala lumpur international airport terminal 1": {
        "name": "Kuala Lumpur International Airport Terminal 1",
        "label": "KLIA Terminal 1",
        "lat": 2.7456,
        "lon": 101.7099,
        "google_place_id": "eldergo:place:klia-t1",
        "formatted_address": "KLIA Terminal 1, Selangor",
    },
}

# Short labels shown in chat and on the route result screen (not full street addresses).
PLACE_UI_LABELS: dict[str, str] = {
    "monash": "Monash University Malaysia",
    "monash uni": "Monash University Malaysia",
    "monash university": "Monash University Malaysia",
    "monash university malaysia": "Monash University Malaysia",
    "klcc": "KLCC",
    "kuala lumpur city centre": "KLCC",
    "kl sentral": "KL Sentral",
    "subang jaya": "Subang Jaya",
    "sunway": "Sunway City",
    "pj": "Petaling Jaya",
}


def place_ui_label(user_query: str, *, google_name: str | None = None, canonical_name: str | None = None) -> str:
    """Pick a short, user-friendly label for route summary and navigation."""
    key = user_query.strip().lower()
    if key in PLACE_UI_LABELS:
        return PLACE_UI_LABELS[key]
    if google_name and len(google_name.strip()) <= 48:
        return google_name.strip()
    if canonical_name:
        canonical_lower = canonical_name.strip().lower()
        for alias, search_name in PLACE_ALIASES.items():
            if search_name.lower() == canonical_lower:
                return PLACE_UI_LABELS.get(alias, search_name)
        if len(canonical_name) <= 48:
            return canonical_name.strip()
    cleaned = user_query.strip()
    return cleaned if cleaned else (google_name or canonical_name or "Place")

GEMINI_ROUTE_PARSE_PROMPT = (
    "You extract Klang Valley travel places from user text for ElderGo KL.\n"
    "Return ONLY valid JSON with keys origin and destination (strings or null).\n"
    "Use full place names suitable for map search in Malaysia.\n"
    "Examples: monash uni -> Monash University Malaysia, klcc -> Kuala Lumpur City Centre.\n"
    "If only one place is mentioned, set the other to null.\n"
    "Do not include markdown or explanation."
)


def normalize_place_query(raw: str) -> str:
    cleaned = raw.strip()
    if not cleaned:
        return cleaned
    key = cleaned.lower()
    return PLACE_ALIASES.get(key, cleaned)


def known_place_key(query: str) -> str:
    return normalize_place_query(query).strip().lower()


def suggest_place_alias(user_query: str) -> str | None:
    """Fuzzy match for typos and abbreviations (monash uni, sentral, etc.)."""
    import difflib

    key = user_query.strip().lower()
    if not key:
        return None
    if key in PLACE_ALIASES:
        return PLACE_ALIASES[key]
    if known_place_key(key) in KNOWN_KV_PLACES:
        return str(KNOWN_KV_PLACES[known_place_key(key)].get("label") or key)

    alias_keys = list(PLACE_ALIASES.keys()) + list(KNOWN_KV_PLACES.keys())
    close = difflib.get_close_matches(key, alias_keys, n=1, cutoff=0.72)
    if close:
        matched = close[0]
        if matched in PLACE_ALIASES:
            return PLACE_ALIASES[matched]
        known = KNOWN_KV_PLACES.get(matched)
        if known:
            return str(known.get("label") or matched)
    return None


def lookup_known_kv_place(query: str) -> dict[str, object] | None:
    """Return cached coordinates for frequent landmarks (no external API)."""
    return KNOWN_KV_PLACES.get(known_place_key(query))


# City-wide queries need Google disambiguation (Sentral vs KLCC vs …), not one centroid.
_BROAD_AREA_PLACE_KEYS = frozenset(
    {
        "kuala lumpur",
        "kl",
        "petaling jaya",
        "pj",
        "subang jaya",
        "shah alam",
        "selangor",
        "wilayah persekutuan",
        "putrajaya",
        "cyberjaya",
    }
)


def is_broad_area_place_query(query: str) -> bool:
    """True when the user named a whole city/region rather than a specific venue."""
    return known_place_key(query) in _BROAD_AREA_PLACE_KEYS


# Landmarks offered when a city-wide query would otherwise auto-resolve to one point.
_BROAD_AREA_DISAMBIG_KEYS: dict[str, tuple[str, ...]] = {
    "kuala lumpur": ("kuala lumpur sentral", "kuala lumpur city centre"),
    "kl": ("kuala lumpur sentral", "kuala lumpur city centre"),
    "petaling jaya": ("petaling jaya",),
    "pj": ("petaling jaya",),
}


def broad_area_disambig_known_places(query: str) -> list[dict[str, object]]:
    keys = _BROAD_AREA_DISAMBIG_KEYS.get(known_place_key(query), ())
    out: list[dict[str, object]] = []
    for key in keys:
        row = KNOWN_KV_PLACES.get(key)
        if row:
            out.append(dict(row))
    return out


def message_has_plan_route_endpoints(message: str) -> bool:
    """True when rules can extract a valid origin/destination pair from one message."""
    if re.search(r"中途", message) or re.search(r"\b(?:along the way|midway)\b", message, re.I):
        return False
    origin, destination = extract_route_endpoints(message)
    if not (origin and destination):
        return False
    return classify_place_input(origin) == "ok" and classify_place_input(destination) == "ok"


def has_single_route_endpoint(message: str) -> bool:
    """True when only origin or only destination is extractable (valid place)."""
    if re.search(r"中途", message) or re.search(r"\b(?:along the way|midway)\b", message, re.I):
        return False
    origin, destination = extract_route_endpoints(message)
    if origin and destination:
        return False
    if origin and classify_place_input(origin) == "ok":
        return True
    if destination and classify_place_input(destination) == "ok":
        return True
    return False


def message_should_use_plan_route(message: str) -> bool:
    return message_has_plan_route_endpoints(message) or has_single_route_endpoint(message)


def _sanitize_endpoint_value(raw: str | None) -> str | None:
    from app.services.ai_route_sentence_service import sanitize_route_endpoint

    return sanitize_route_endpoint(raw)


def classify_place_input(raw: str) -> PlaceInputIssue:
    """Classify a single place field (not a full chat turn) for validation messaging."""
    cleaned = raw.strip()
    if not cleaned:
        return "empty"
    lowered = cleaned.lower()
    if lowered in {"?", "!", ".", "what", "huh", "idk", "dunno", "help"}:
        return "too_short"
    if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", cleaned):
        return "too_short"
    if lowered in PLACE_ALIASES or known_place_key(cleaned) in KNOWN_KV_PLACES:
        return "ok"

    if _ROUTE_QUESTION_HINT.search(cleaned) or re.search(r"\bfrom\b.*\bto\b", cleaned, re.I):
        origin, destination = extract_route_endpoints(cleaned)
        if origin and destination:
            if is_plausible_place_query(origin) and is_plausible_place_query(destination):
                return "route_sentence"

    if len(cleaned) <= 2:
        return "too_short"
    if len(cleaned) > 72:
        if _ROUTE_QUESTION_HINT.search(cleaned):
            return "route_sentence"
        return "too_long"
    if not is_plausible_place_query(cleaned):
        return "implausible"
    return "ok"


def refine_place_query_for_slot(message: str, slot: PlaceSlotKind) -> str:
    """When the user pastes a full route sentence into one slot, keep only that endpoint."""
    origin, destination = extract_route_endpoints(message)
    if slot == "origin" and origin:
        return origin
    if slot == "destination" and destination:
        return destination
    return message.strip()


def is_unclear_place_reply(message: str) -> bool:
    issue = classify_place_input(message)
    if issue == "route_sentence":
        return False
    return issue != "ok"


def is_plausible_place_query(raw: str) -> bool:
    """Reject gibberish or accidental substring matches (e.g. 'AA' inside Chinese text)."""
    cleaned = raw.strip()
    if not cleaned:
        return False
    key = cleaned.lower()
    if key in PLACE_ALIASES:
        return True
    if key in {"kl", "pj"}:
        return True

    latin_tokens = re.findall(r"[A-Za-z0-9]+", cleaned)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", cleaned)

    if cjk_chars and latin_tokens:
        # Mixed scripts with only short Latin fragments are usually typos, not place names.
        if not any(len(token) >= 3 for token in latin_tokens):
            return False

    if cjk_chars and not latin_tokens:
        return len(cjk_chars) >= 2

    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9\s.'-]{0,72}$", cleaned):
        return False

    if not latin_tokens:
        return False
    if any(len(token) >= 3 for token in latin_tokens):
        return True
    return False


def place_matches_user_query(user_query: str, *, place_name: str | None, formatted_address: str | None) -> bool:
    """Require meaningful overlap between user text and the resolved Google place."""
    if not is_plausible_place_query(user_query):
        return False
    query_key = user_query.strip().lower()
    if query_key in PLACE_ALIASES:
        return True

    haystack = " ".join(
        part for part in (place_name or "", formatted_address or "") if part
    ).lower()
    if not haystack:
        return False

    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]{3,}", user_query)]
    if not tokens:
        return True
    return any(token in haystack for token in tokens)


def try_rule_route_pair(message: str) -> tuple[str | None, str | None]:
    from app.services.ai_route_sentence_service import parse_route_sentence

    parsed = parse_route_sentence(message)
    return parsed.origin, parsed.destination


async def try_gemini_route_pair(
    message: str,
    *,
    origin_hint: str | None = None,
    destination_hint: str | None = None,
) -> tuple[str | None, str | None]:
    from app.services.gemini_client import call_with_key_pool, extract_text_from_response, parse_json_from_text

    context_parts = [f"User message: {message}"]
    if origin_hint:
        context_parts.append(f"Known origin so far: {origin_hint}")
    if destination_hint:
        context_parts.append(f"Known destination so far: {destination_hint}")
    context_parts.append('Return JSON like {"origin":"...","destination":"..."}')

    prompt = f"{GEMINI_ROUTE_PARSE_PROMPT}\n\n" + "\n".join(context_parts)
    data, error_kind = await call_with_key_pool(prompt, timeout=12.0)
    if error_kind or not data:
        return None, None
    try:
        text = extract_text_from_response(data)
        parsed = parse_json_from_text(text)
        if not parsed:
            return None, None
        origin = _sanitize_endpoint_value(
            str(origin).strip() if origin else None
        )
        destination = _sanitize_endpoint_value(
            str(destination).strip() if destination else None
        )
        return origin, destination
    except Exception:
        return None, None
