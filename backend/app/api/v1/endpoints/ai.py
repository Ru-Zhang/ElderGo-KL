import re
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

import httpx
from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.ai import AIConversationResponse, AIMessageRequest, AIMessageResponse
from app.services.ai_grounding_service import GroundedContext, build_grounded_context
from app.services.ai_guardrail_service import is_in_scope

router = APIRouter()
settings = get_settings()

GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)
OUT_OF_SCOPE_MARKER = "[OUT_OF_SCOPE]"
SUPPORTED_GUARDRAIL_MODES = {"hybrid", "rules_only", "prompt_only"}

GUARDRAIL_PROMPT = (
    "You are ElderGo KL assistant. Only answer ElderGo KL transport support topics: routes, stations, "
    "accessibility, tickets/fares/concessions, privacy, and app usage. "
    f"If the user request is outside this scope, start the response with {OUT_OF_SCOPE_MARKER} and provide no "
    "extra content beyond a short refusal. "
    "Reply in the same language as the user (English, Chinese, or Malay). "
    "Do not invent live data you cannot verify; clearly state unknown when needed. "
    "Write in an elderly-friendly style: short and clear sentences, plain words, and calm tone. "
    "Format with this structure: Summary (1 short sentence), Steps (2-4 bullet points), Next step (1 action line). "
    "Keep total response around 4-8 lines and avoid long paragraphs. "
    "If a technical term is required, explain it in simple words in the same line."
)
CONTEXTUAL_GUARDRAIL_PROMPT = (
    f"{GUARDRAIL_PROMPT} "
    "When grounded context is provided, use only the provided project facts for concrete claims. "
    "Do not add unsupported details, prices, or live operational facts. "
    "If context is missing for a detail, explicitly say unknown / not found in project data."
)

OUT_OF_SCOPE_TEMPLATES = {
    "zh": (
        "我目前只能协助 ElderGo KL 的路线、站点、无障碍、票务优惠、隐私与 App 使用问题。\n"
        "下一步：请把问题改成以上主题，我会一步一步协助你。"
    ),
    "ms": (
        "Saya hanya boleh bantu topik ElderGo KL: laluan, stesen, kebolehcapaian, tiket/konsesi, privasi, dan penggunaan aplikasi.\n"
        "Langkah seterusnya: ubah soalan kepada topik ini, saya akan bantu langkah demi langkah."
    ),
    "en": (
        "I can only help with ElderGo KL routes, stations, accessibility, tickets, concession information, privacy, and app usage.\n"
        "Next step: ask your question in one of these topics, and I will guide you step by step."
    ),
}

FALLBACK_TEMPLATES = {
    "zh": (
        "抱歉，AI 助手暂时不可用。\n"
        "下一步：请 1 分钟后再试，或换一个更短的问题。"
    ),
    "ms": (
        "Maaf, pembantu AI tidak tersedia buat sementara waktu.\n"
        "Langkah seterusnya: cuba semula dalam 1 minit, atau gunakan soalan yang lebih ringkas."
    ),
    "en": (
        "Sorry, the AI assistant is temporarily unavailable.\n"
        "Next step: try again in 1 minute, or ask a shorter question."
    ),
}

NEXT_STEP_PREFIX = {
    "zh": "下一步：",
    "ms": "Langkah seterusnya:",
    "en": "Next step:",
}

NEXT_STEP_DEFAULT = {
    "zh": "下一步：请告诉我你的出发地和目的地，我会给你清晰步骤。",
    "ms": "Langkah seterusnya: beritahu tempat mula dan destinasi anda, saya akan beri langkah yang jelas.",
    "en": "Next step: tell me your start point and destination, and I will give clear steps.",
}

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？.!?])\s+")
MAP_DISCLAIMER_TEXT = "数据来源于地图服务，可能有变动"

GEO_INTENT_PATTERNS = (
    # Nearby / proximity queries.
    r"\bnearby\b",
    r"\bnear me\b",
    r"\bclosest\b",
    r"附近",
    r"就近",
    r"\bdekat\b",
    r"\bberhampiran\b",
    # Route / navigation queries.
    r"\bhow to get to\b",
    r"\bhow do i get to\b",
    r"\bway to\b",
    r"\bdirections?\b",
    r"怎么去",
    r"如何去",
    r"到.*怎么走",
    r"\bcara pergi\b",
    r"\bmacam mana pergi\b",
    # Distance / duration.
    r"\bdistance\b",
    r"\bhow far\b",
    r"\bhow long\b",
    r"多远",
    r"距离",
    r"多久",
    r"\bjarak\b",
    r"\bberapa jauh\b",
    r"\bberapa lama\b",
    # POI / address style lookup.
    r"\baddress\b",
    r"\bwhere is\b",
    r"\blocation\b",
    r"地址",
    r"在哪",
    r"\balamat\b",
    r"\bdi mana\b",
)


class GeminiKeyPool:
    def __init__(self) -> None:
        self._lock = Lock()
        self._exhausted_until: dict[str, datetime] = {}
        self._cursor = 0

    @staticmethod
    def _local_day_end_utc() -> datetime:
        # Align reset with Malaysia local day (UTC+8) for daily free-tier quotas.
        tz = timezone(timedelta(hours=8))
        now_local = datetime.now(tz=tz)
        next_day_start = datetime.combine(
            (now_local + timedelta(days=1)).date(),
            datetime.min.time(),
            tzinfo=tz,
        )
        return next_day_start.astimezone(timezone.utc)

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429

    @staticmethod
    def _collect_unique_keys() -> list[str]:
        keys: list[str] = []
        seen: set[str] = set()

        for key in [settings.gemini_api_key_primary, settings.gemini_api_key_secondary]:
            cleaned = (key or "").strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                keys.append(cleaned)

        for key in (settings.gemini_api_keys or "").split(","):
            cleaned = key.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                keys.append(cleaned)

        return keys

    def get_available_keys(self) -> list[str]:
        now_utc = datetime.now(timezone.utc)
        with self._lock:
            self._exhausted_until = {
                key: until for key, until in self._exhausted_until.items() if until > now_utc
            }
            keys = self._collect_unique_keys()
            available = [key for key in keys if key not in self._exhausted_until]
            if not available:
                return []

            start = self._cursor % len(available)
            rotated = available[start:] + available[:start]
            self._cursor = (self._cursor + 1) % len(available)
            return rotated

    def mark_exhausted_today(self, key: str) -> None:
        with self._lock:
            self._exhausted_until[key] = self._local_day_end_utc()


GEMINI_KEY_POOL = GeminiKeyPool()


def _detect_language(message: str) -> str:
    if any("\u4e00" <= ch <= "\u9fff" for ch in message):
        return "zh"

    lowered = message.lower()
    malay_hints = (" saya ", " dan ", " bagaimana ", " stesen ", " laluan ", " tiket ", " boleh ")
    padded = f" {lowered} "
    if any(hint in padded for hint in malay_hints):
        return "ms"
    return "en"


def _out_of_scope_answer_for(message: str) -> str:
    return OUT_OF_SCOPE_TEMPLATES[_detect_language(message)]


def _fallback_answer_for(message: str) -> str:
    return FALLBACK_TEMPLATES[_detect_language(message)]


def _guardrail_mode() -> str:
    mode = (settings.ai_guardrail_mode or "hybrid").strip().lower()
    if mode not in SUPPORTED_GUARDRAIL_MODES:
        return "hybrid"
    return mode


def _is_geographic_query(message: str) -> bool:
    text = message.strip().lower()
    if not text:
        return False
    return any(re.search(pattern, text) for pattern in GEO_INTENT_PATTERNS)


def _maps_grounding_enabled_for_message(message: str) -> bool:
    return settings.gemini_maps_grounding_enabled and _is_geographic_query(message)


def _append_maps_disclaimer(answer: str) -> str:
    if MAP_DISCLAIMER_TEXT in answer:
        return answer
    normalized = answer.rstrip()
    if not normalized:
        return MAP_DISCLAIMER_TEXT
    return f"{normalized}\n{MAP_DISCLAIMER_TEXT}"


def _call_gemini(
    message: str,
    api_key: str,
    prompt_guardrail: bool,
    grounded_context: GroundedContext | None = None,
) -> str:
    if not api_key:
        raise ValueError("Gemini API key is missing.")

    url = GEMINI_API_URL_TEMPLATE.format(model=settings.gemini_model, api_key=api_key)
    user_prompt = message
    if prompt_guardrail:
        if grounded_context and grounded_context.facts:
            facts_text = "\n".join(f"- {fact}" for fact in grounded_context.facts)
            user_prompt = (
                f"{CONTEXTUAL_GUARDRAIL_PROMPT}\n\n"
                f"Grounded context ({grounded_context.response_source}, intent={grounded_context.intent}):\n"
                f"{facts_text}\n\n"
                f"User message:\n{message}"
            )
        else:
            user_prompt = (
                f"{GUARDRAIL_PROMPT}\n\n"
                "Project data context: none matched for this message. "
                "Provide general guidance and clearly mark unknown details.\n\n"
                f"User message:\n{message}"
            )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ]
    }
    if _maps_grounding_enabled_for_message(message):
        maps_tool: dict[str, bool] = {}
        if settings.gemini_maps_grounding_enable_widget:
            maps_tool["enableWidget"] = True
        payload["tools"] = [{"googleMaps": maps_tool}]
        payload["toolConfig"] = {
            "retrievalConfig": {
                "latLng": {
                    "latitude": settings.gemini_maps_grounding_default_latitude,
                    "longitude": settings.gemini_maps_grounding_default_longitude,
                }
            }
        }

    response = httpx.post(url, json=payload, timeout=20.0)
    response.raise_for_status()
    data = response.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini response has no candidates.")

    parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    answer = "\n".join(text_parts).strip()
    if not answer:
        raise ValueError("Gemini response text is empty.")
    return answer


def _normalize_elder_friendly_answer(answer: str, language: str) -> str:
    normalized_lines = [line.strip() for line in answer.replace("\r\n", "\n").split("\n") if line.strip()]
    if not normalized_lines:
        return NEXT_STEP_DEFAULT[language]

    compressed = " ".join(normalized_lines)
    compressed = re.sub(r"\s+", " ", compressed).strip()
    sentences = [segment.strip() for segment in SENTENCE_SPLIT_PATTERN.split(compressed) if segment.strip()]

    if len(sentences) >= 2 and len(normalized_lines) <= 2:
        condensed = [sentences[0]]
        for sentence in sentences[1:4]:
            condensed.append(f"- {sentence}")
        normalized_lines = condensed
    else:
        normalized_lines = normalized_lines[:8]

    has_next_step = any(
        line.lower().startswith(NEXT_STEP_PREFIX["en"].lower())
        or line.startswith(NEXT_STEP_PREFIX["zh"])
        or line.lower().startswith(NEXT_STEP_PREFIX["ms"].lower())
        for line in normalized_lines
    )
    if not has_next_step:
        normalized_lines.append(NEXT_STEP_DEFAULT[language])

    return "\n".join(normalized_lines[:8])


def _generate_answer_with_fallback(
    message: str,
    prompt_guardrail: bool,
    grounded_context: GroundedContext | None = None,
) -> tuple[str, bool]:
    keys = GEMINI_KEY_POOL.get_available_keys()
    last_error: Exception | None = None

    if not keys:
        return _fallback_answer_for(message), False

    for key in keys:
        try:
            answer = _call_gemini(
                message=message,
                api_key=key,
                prompt_guardrail=prompt_guardrail,
                grounded_context=grounded_context,
            )
            if answer.startswith(OUT_OF_SCOPE_MARKER):
                return _out_of_scope_answer_for(message), True
            return _normalize_elder_friendly_answer(answer, _detect_language(message)), False
        except Exception as exc:  # Keep endpoint resilient for UI demo flow.
            last_error = exc
            if GeminiKeyPool._is_rate_limit_error(exc):
                GEMINI_KEY_POOL.mark_exhausted_today(key)
            continue

    if last_error is not None:
        return _fallback_answer_for(message), False
    return _fallback_answer_for(message), False


@router.post("/conversations", response_model=AIConversationResponse)
def create_conversation() -> AIConversationResponse:
    # Lightweight stateless conversation id for UI threading in demo mode.
    return AIConversationResponse(conversation_id=f"conv_{uuid4().hex[:16]}")


@router.post("/conversations/{conversation_id}/messages", response_model=AIMessageResponse)
def send_message(conversation_id: str, payload: AIMessageRequest) -> AIMessageResponse:
    mode = _guardrail_mode()
    rules_in_scope = is_in_scope(payload.message)

    if settings.ai_guardrail_enabled and (mode == "rules_only" or settings.ai_guardrail_strict) and (not rules_in_scope):
        return AIMessageResponse(
            conversation_id=conversation_id,
            in_scope=False,
            answer=_out_of_scope_answer_for(payload.message),
            response_source="fallback",
            grounded=False,
            used_data_keys=[],
        )

    grounded_context = build_grounded_context(
        message=payload.message,
        current_route_id=payload.current_route_id,
        selected_location_id=payload.selected_location_id,
        anonymous_user_id=payload.anonymous_user_id,
    )
    prompt_guardrail = settings.ai_guardrail_enabled and mode in {"hybrid", "prompt_only"}
    maps_grounding_used = _maps_grounding_enabled_for_message(payload.message)
    answer, model_out_of_scope = _generate_answer_with_fallback(
        payload.message,
        prompt_guardrail=prompt_guardrail,
        grounded_context=grounded_context,
    )
    if maps_grounding_used:
        answer = _append_maps_disclaimer(answer)
    if settings.ai_guardrail_enabled and model_out_of_scope:
        return AIMessageResponse(
            conversation_id=conversation_id,
            in_scope=False,
            answer=answer,
            response_source=grounded_context.response_source if grounded_context.grounded else "fallback",
            grounded=grounded_context.grounded,
            used_data_keys=grounded_context.used_data_keys,
        )

    response_source = grounded_context.response_source if grounded_context.grounded else "fallback"
    return AIMessageResponse(
        conversation_id=conversation_id,
        in_scope=rules_in_scope if settings.ai_guardrail_enabled and mode == "rules_only" else True,
        answer=answer,
        response_source=response_source,
        grounded=grounded_context.grounded,
        used_data_keys=grounded_context.used_data_keys,
    )
