"""Lightweight Gemini JSON extraction for travel intent and route slots (low token)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.core.config import get_settings
from app.services.ai_intent_service import classify_intent
from app.services.ai_route_parse_service import try_rule_route_pair
from app.services.ai_route_sentence_service import (
    extract_preference_hint,
    has_departure_signal,
    parse_departure_time,
    parse_route_sentence,
)
from app.services.gemini_client import (
    GEMINI_KEY_POOL,
    call_with_key_pool,
    extract_text_from_response,
    parse_json_from_text,
)

TravelIntent = Literal[
    "route_planning",
    "route_recommendation",
    "exploratory_poi",
    "weather",
    "station_info",
    "general",
]

GEMINI_TRAVEL_SLOTS_PROMPT = (
    "You extract travel intent and places for ElderGo KL (Klang Valley, Malaysia only).\n"
    "Return ONLY valid JSON with keys:\n"
    '  intent: "route_planning"|"route_recommendation"|"exploratory_poi"|"weather"|"station_info"|"general"\n'
    "  origin: string or null\n"
    "  destination: string or null\n"
    "  departure: string or null (e.g. tomorrow 1pm, at 11:30 — keep user wording)\n"
    "  preference: string or null (accessibility_first|least_walk|fewest_transfers)\n"
    "Use full Malaysian place names. If only destination, origin null. No markdown."
)

_GREETING_RE = re.compile(
    r"^(?:hi|hello|hey|thanks|thank you|ok|okay)[.!?]*$",
    re.I,
)


@dataclass
class TravelSlots:
    intent: TravelIntent
    origin: str | None = None
    destination: str | None = None
    departure: str | None = None
    preference: str | None = None


def _should_skip_gemini(message: str, classified: str) -> bool:
    settings = get_settings()
    if not getattr(settings, "gemini_intent_routing_enabled", True):
        return True
    if not GEMINI_KEY_POOL.has_configured_keys():
        return True
    stripped = message.strip()
    if len(stripped) < 4 or _GREETING_RE.match(stripped):
        return True
    if classified in {"ticket_guide", "concession_guide", "privacy", "preference", "out_of_scope"}:
        return True
    parsed = parse_route_sentence(message)
    if parsed.origin and parsed.destination and (parsed.departure or has_departure_signal(message)):
        return True
    if classified in {"weather", "station_info", "planning"}:
        return True
    from app.services.ai_quick_question_service import match_quick_question, is_flow_quick_question

    quick = match_quick_question(message)
    if quick and is_flow_quick_question(quick.question_id):
        return True
    return False


def _infer_rule_travel_slots(message: str, classified: str) -> TravelSlots | None:
    """Rules-only travel intent (route slots, weather, station, plan chip)."""
    route_slots = _merge_rule_slots(message)
    if route_slots:
        return route_slots

    from app.services.ai_intent_service import STATION_PATTERNS, WEATHER_PATTERNS, _matches_any
    from app.services.ai_quick_question_service import match_quick_question

    if classified == "weather" or _matches_any(message, WEATHER_PATTERNS):
        return TravelSlots(intent="weather")
    if classified == "station_info" or _matches_any(message, STATION_PATTERNS):
        return TravelSlots(intent="station_info")

    quick = match_quick_question(message)
    if quick:
        if quick.question_id == "weather":
            return TravelSlots(intent="weather")
        if quick.question_id == "station_info":
            return TravelSlots(intent="station_info")
        if quick.question_id == "plan_route":
            return TravelSlots(intent="route_planning")
    return None


def _merge_rule_slots(message: str) -> TravelSlots | None:
    from app.services.ai_route_sentence_service import sanitize_route_endpoint

    parsed = parse_route_sentence(message)
    origin, dest = parsed.origin, parsed.destination
    if not origin and not dest:
        rule_origin, rule_dest = try_rule_route_pair(message)
        origin, dest = rule_origin, rule_dest
    if not origin and not dest:
        return None
    dep = parsed.departure or (parse_departure_time(message) if has_departure_signal(message) else None)
    pref = extract_preference_hint(message)
    return TravelSlots(
        intent="route_planning",
        origin=sanitize_route_endpoint(origin),
        destination=sanitize_route_endpoint(dest),
        departure=dep,
        preference=pref,
    )


async def try_gemini_travel_slots(
    message: str,
    *,
    origin_hint: str | None = None,
    destination_hint: str | None = None,
    classified: str | None = None,
) -> TravelSlots | None:
    """Extract intent + slots via rules first, then a short Gemini call if needed."""
    from app.schemas.ai import AIMessageRequest

    intent_class = classified or classify_intent(message, AIMessageRequest(message=message))
    if _should_skip_gemini(message, intent_class):
        return _infer_rule_travel_slots(message, intent_class)

    rule_slots = _merge_rule_slots(message)
    if rule_slots and rule_slots.origin and rule_slots.destination:
        return rule_slots

    context = [f"User message: {message}"]
    if origin_hint:
        context.append(f"Known origin: {origin_hint}")
    if destination_hint:
        context.append(f"Known destination: {destination_hint}")
    prompt = f"{GEMINI_TRAVEL_SLOTS_PROMPT}\n\n" + "\n".join(context)

    data, error_kind = await call_with_key_pool(prompt, timeout=12.0, max_output_tokens=128)
    if error_kind or not data:
        return rule_slots

    try:
        text = extract_text_from_response(data)
        parsed = parse_json_from_text(text)
        if not parsed:
            return rule_slots
        raw_intent = str(parsed.get("intent") or "route_planning").strip().lower()
        intent: TravelIntent = "route_planning"
        if raw_intent in {
            "route_planning",
            "route_recommendation",
            "exploratory_poi",
            "weather",
            "station_info",
            "general",
        }:
            intent = raw_intent  # type: ignore[assignment]

        origin = parsed.get("origin")
        destination = parsed.get("destination")
        departure = parsed.get("departure")
        preference = parsed.get("preference")
        from app.services.ai_route_sentence_service import sanitize_route_endpoint

        gemini_slots = TravelSlots(
            intent=intent,
            origin=sanitize_route_endpoint(str(origin).strip() if origin else None),
            destination=sanitize_route_endpoint(
                str(destination).strip() if destination else None
            ),
            departure=str(departure).strip() if departure else None,
            preference=str(preference).strip() if preference else None,
        )
        if rule_slots:
            return TravelSlots(
                intent=gemini_slots.intent or rule_slots.intent,
                origin=rule_slots.origin or gemini_slots.origin,
                destination=rule_slots.destination or gemini_slots.destination,
                departure=rule_slots.departure or gemini_slots.departure,
                preference=rule_slots.preference or gemini_slots.preference,
            )
        return gemini_slots
    except Exception:
        return rule_slots


def is_route_recommendation_message(message: str) -> bool:
    lowered = message.lower().strip()
    patterns = (
        r"\b(?:route|trip|travel)\s+recommendation\b",
        r"\brecommend\s+(?:a\s+)?(?:route|trip|way)\b",
        r"\bbest\s+way\s+to\s+(?:get|go|travel)\b",
        r"\bsuggest\s+(?:a\s+)?route\b",
        r"\bhow\s+should\s+i\s+(?:get|go|travel)\b",
        r"路线推荐",
        r"推荐.*路线",
        r"\bcadangan\s+laluan\b",
    )
    return any(re.search(p, lowered) for p in patterns)
