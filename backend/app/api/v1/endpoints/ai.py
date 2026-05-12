import re
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

import httpx
from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.ai import AIConversationResponse, AIMessageRequest, AIMessageResponse
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
    "Use a natural structure: one short answer first, then 2-4 simple bullet points only when useful. "
    "End with one gentle practical suggestion, but do not force labels like Summary, Steps, or Next step. "
    "Keep total response around 4-8 lines and avoid long paragraphs. "
    "If a technical term is required, explain it in simple words in the same line."
)
PROJECT_CAPABILITY_PROMPT = (
    "Project capability boundary for ElderGo KL:\n"
    "Implemented in the app: plan a route, set travel preferences, show recommended route steps, "
    "show weather guidance for a planned route, view station/accessibility/facility/address/opening-hours information, "
    "save or share a route, open Google Maps for navigation, view a ticket-buying guide, view a senior concession "
    "application guide, view privacy information, clear local cache/preferences, and answer questions about these features.\n"
    "Not implemented in the app: buying tickets, topping up cards, making payments, buying tokens, calculating or charging "
    "live fares, applying for or submitting concession forms, ride hailing, contacting or calling station staff, guaranteeing "
    "live train operating status, or completing real-name account services.\n"
    "For ticket and concession questions, say the app provides guidance or information only. Never say users can buy tickets, "
    "pay, top up, buy tokens, or apply for concession inside ElderGo KL.\n"
    "For unsupported actions, clearly say they cannot be completed in the app, then give an available alternative such as "
    "viewing the guide, using the station machine/counter, following official channels, or opening Google Maps.\n"
    "Do not promise buttons, pages, transactions, live data, calls, or services that are not listed as implemented. "
    "If unsure whether ElderGo KL can do something, treat it as not supported in the app."
)
OUT_OF_SCOPE_TEMPLATES = {
    "zh": (
        "我目前只能协助 ElderGo KL 的路线、站点、无障碍、票务优惠、隐私与 App 使用问题。\n"
        "你可以把问题改成以上主题，我会一步一步协助你。"
    ),
    "ms": (
        "Saya hanya boleh bantu topik ElderGo KL: laluan, stesen, kebolehcapaian, tiket/konsesi, privasi, dan penggunaan aplikasi.\n"
        "Tanya tentang salah satu topik ini, dan saya akan bantu langkah demi langkah."
    ),
    "en": (
        "I can only help with ElderGo KL routes, stations, accessibility, tickets, concession information, privacy, and app usage.\n"
        "Ask about one of these topics, and I will guide you step by step."
    ),
}

FALLBACK_TEMPLATES = {
    "zh": (
        "抱歉，AI 助手暂时不可用。\n"
        "请 1 分钟后再试，或换一个更短的问题。"
    ),
    "ms": (
        "Maaf, pembantu AI tidak tersedia buat sementara waktu.\n"
        "Cuba semula dalam 1 minit, atau gunakan soalan yang lebih ringkas."
    ),
    "en": (
        "Sorry, the AI assistant is temporarily unavailable.\n"
        "Please try again in 1 minute, or ask a shorter question."
    ),
}

QUOTA_EXHAUSTED_TEMPLATES = {
    "zh": (
        "今天的 AI 使用额度暂时用完了。\n"
        "请晚一点再试；你也可以先使用路线规划、站点资料和 Help 里的指南。"
    ),
    "ms": (
        "Kuota AI untuk hari ini telah habis buat sementara waktu.\n"
        "Sila cuba lagi kemudian; anda masih boleh guna perancangan laluan, maklumat stesen, dan panduan Help."
    ),
    "en": (
        "The AI usage limit is temporarily used up for today.\n"
        "Please try again later; you can still use route planning, station details, and the Help guides."
    ),
}

ACTION_CUE_PREFIXES = {
    "zh": ("下一步：", "请", "你可以", "建议", "如果"),
    "ms": ("Langkah seterusnya:", "Sila ", "Anda boleh ", "Cuba ", "Jika "),
    "en": ("Next step:", "Please ", "You can ", "Try ", "If "),
}

ACTION_SUGGESTION_DEFAULT = {
    "zh": "你可以告诉我出发地和目的地，我会帮你整理清楚步骤。",
    "ms": "Anda boleh beritahu tempat mula dan destinasi, saya akan susun langkah yang jelas.",
    "en": "You can tell me your start point and destination, and I will keep the steps clear.",
}

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？.!?])\s+")
UNSUPPORTED_TICKET_PATTERNS = (
    re.compile(r"\b(?:buy|purchase|get)\s+(?:a\s+)?tickets?\s+(?:in|inside|through|from|using|with)\s+(?:the\s+)?(?:app|eldergo)", re.I),
    re.compile(r"\b(?:the\s+)?(?:app|eldergo)\s+(?:can|lets you|allows you to)\s+(?:buy|purchase|get)\s+(?:a\s+)?tickets?", re.I),
    re.compile(r"\b(?:pay|top up|reload|buy tokens?)\s+(?:in|inside|through|from|using|with)\s+(?:the\s+)?(?:app|eldergo)", re.I),
    re.compile(r"(?:在|通过|使用).*(?:app|ElderGo|eldergo).*买票", re.I),
    re.compile(r"(?:app|ElderGo|eldergo).*可以买票", re.I),
    re.compile(r"(?:在|通过|使用).*(?:app|ElderGo|eldergo).*(?:充值|付款|购买代币)", re.I),
    re.compile(r"\bbeli\s+tiket\b.*\b(?:aplikasi|eldergo)\b", re.I),
    re.compile(r"\b(?:aplikasi|eldergo)\b.*\bboleh\s+beli\s+tiket\b", re.I),
)
UNSUPPORTED_CONCESSION_PATTERNS = (
    re.compile(r"\bapply\s+(?:for\s+)?(?:a\s+)?(?:senior\s+)?concession\s+(?:in|inside|through|from|using|with)\s+(?:the\s+)?(?:app|eldergo)", re.I),
    re.compile(r"\b(?:the\s+)?(?:app|eldergo)\s+(?:can|lets you|allows you to)\s+(?:apply|submit).*\bconcession\b", re.I),
    re.compile(r"(?:在|通过|使用).*(?:app|ElderGo|eldergo).*申请.*(?:优惠|concession|折扣)", re.I),
    re.compile(r"(?:app|ElderGo|eldergo).*可以.*申请.*(?:优惠|concession|折扣)", re.I),
    re.compile(r"\bmohon\s+konsesi\b.*\b(?:aplikasi|eldergo)\b", re.I),
    re.compile(r"\b(?:aplikasi|eldergo)\b.*\bboleh\s+mohon\s+konsesi\b", re.I),
)
UNSUPPORTED_STAFF_CONTACT_PATTERNS = (
    re.compile(r"\b(?:call|contact|message)\s+(?:station\s+)?staff\s+(?:in|inside|through|from|using|with)\s+(?:the\s+)?(?:app|eldergo)", re.I),
    re.compile(r"\b(?:the\s+)?(?:app|eldergo)\s+(?:can|lets you|allows you to)\s+(?:call|contact|message)\s+(?:station\s+)?staff", re.I),
    re.compile(r"(?:在|通过|使用).*(?:app|ElderGo|eldergo).*(?:联系|拨打|呼叫).*工作人员", re.I),
    re.compile(r"(?:app|ElderGo|eldergo).*可以.*(?:联系|拨打|呼叫).*工作人员", re.I),
    re.compile(r"\b(?:hubungi|telefon)\s+staf\s+stesen\b.*\b(?:aplikasi|eldergo)\b", re.I),
)

UNSUPPORTED_TEMPLATES = {
    "ticket": {
        "zh": (
            "ElderGo KL 只提供买票指南，不能在 App 内买票、充值或付款。\n"
            "- 你可以在 Help 页面查看买票步骤。\n"
            "- 实际买票请使用车站售票机、柜台或 Touch 'n Go 卡。\n"
            "建议先打开买票指南，出发前看一遍步骤会更安心。"
        ),
        "ms": (
            "ElderGo KL hanya menyediakan panduan membeli tiket; ia tidak boleh menjual tiket, tambah nilai, atau menerima bayaran dalam app.\n"
            "- Anda boleh baca panduan tiket di Help.\n"
            "- Beli tiket di mesin, kaunter stesen, atau gunakan kad Touch 'n Go.\n"
            "Anda boleh buka panduan tiket sebelum bergerak supaya langkah di stesen terasa lebih biasa."
        ),
        "en": (
            "ElderGo KL only provides ticket-buying information; it cannot sell tickets, top up, or take payment in the app.\n"
            "- Open the ticket guide in Help for simple steps.\n"
            "- Buy tickets at station machines, counters, or use a Touch 'n Go card.\n"
            "You can view the ticket guide before you travel, so the station steps feel familiar."
        ),
    },
    "concession": {
        "zh": (
            "ElderGo KL 只提供长者优惠申请信息，不能在 App 内提交申请。\n"
            "- 你可以在 Help 页面查看需要准备的文件和步骤。\n"
            "- 实际申请请按指南到柜台或官方渠道办理。\n"
            "建议先打开长者优惠指南，把 MyKad 准备好。"
        ),
        "ms": (
            "ElderGo KL hanya menyediakan panduan konsesi warga emas; ia tidak boleh menghantar permohonan dalam app.\n"
            "- Anda boleh baca panduan konsesi di Help.\n"
            "- Mohon melalui kaunter atau saluran rasmi yang ditunjukkan dalam panduan.\n"
            "Anda boleh buka panduan konsesi dahulu dan sediakan MyKad."
        ),
        "en": (
            "ElderGo KL only provides senior concession information; it cannot submit an application in the app.\n"
            "- Open the concession guide in Help to see what to prepare.\n"
            "- Apply at the counter or official channel shown in the guide.\n"
            "You can view the concession guide first and prepare your MyKad."
        ),
    },
    "staff": {
        "zh": (
            "ElderGo KL 不能在 App 内联系或拨打车站工作人员。\n"
            "- App 可以显示路线和站点信息。\n"
            "- 如需人工帮助，请到车站柜台或向现场工作人员询问。\n"
            "你可以先查看相关站点信息，抵达后再向工作人员求助。"
        ),
        "ms": (
            "ElderGo KL tidak boleh menelefon atau menghubungi staf stesen dari app.\n"
            "- App boleh tunjukkan maklumat laluan dan stesen.\n"
            "- Untuk bantuan manusia, pergi ke kaunter stesen atau tanya staf di lokasi.\n"
            "Anda boleh semak butiran stesen dahulu, kemudian minta bantuan staf apabila tiba."
        ),
        "en": (
            "ElderGo KL cannot call or contact station staff from the app.\n"
            "- The app can show route and station information.\n"
            "- For human help, go to the station counter or ask staff on site.\n"
            "You can check the station details first, then ask staff when you arrive."
        ),
    },
}


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

    def has_configured_keys(self) -> bool:
        return bool(self._collect_unique_keys())

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


def _quota_exhausted_answer_for(message: str) -> str:
    return QUOTA_EXHAUSTED_TEMPLATES[_detect_language(message)]


def _guardrail_mode() -> str:
    mode = (settings.ai_guardrail_mode or "hybrid").strip().lower()
    if mode not in SUPPORTED_GUARDRAIL_MODES:
        return "hybrid"
    return mode


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _unsupported_feature_answer_for(message: str, answer: str) -> str | None:
    combined = f"{message}\n{answer}"
    language = _detect_language(message)

    if _matches_any(combined, UNSUPPORTED_TICKET_PATTERNS):
        return UNSUPPORTED_TEMPLATES["ticket"][language]
    if _matches_any(combined, UNSUPPORTED_CONCESSION_PATTERNS):
        return UNSUPPORTED_TEMPLATES["concession"][language]
    if _matches_any(combined, UNSUPPORTED_STAFF_CONTACT_PATTERNS):
        return UNSUPPORTED_TEMPLATES["staff"][language]
    return None


def _call_gemini(
    message: str,
    api_key: str,
    prompt_guardrail: bool,
) -> str:
    if not api_key:
        raise ValueError("Gemini API key is missing.")

    url = GEMINI_API_URL_TEMPLATE.format(model=settings.gemini_model, api_key=api_key)
    user_prompt = message
    if prompt_guardrail:
        user_prompt = f"{GUARDRAIL_PROMPT}\n\n{PROJECT_CAPABILITY_PROMPT}\n\nUser message:\n{message}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ]
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
        return ACTION_SUGGESTION_DEFAULT[language]

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

    action_cues = ACTION_CUE_PREFIXES[language]
    if isinstance(action_cues, str):
        action_cues = (action_cues,)
    has_action_suggestion = any(
        line.lower().startswith(tuple(cue.lower() for cue in action_cues))
        for line in normalized_lines
    )
    if not has_action_suggestion:
        normalized_lines.append(ACTION_SUGGESTION_DEFAULT[language])

    return "\n".join(normalized_lines[:8])


def _generate_answer_with_fallback(
    message: str,
    prompt_guardrail: bool,
) -> tuple[str, bool]:
    keys = GEMINI_KEY_POOL.get_available_keys()
    last_error: Exception | None = None
    rate_limit_errors = 0

    if not keys:
        if GEMINI_KEY_POOL.has_configured_keys():
            return _quota_exhausted_answer_for(message), False
        return _fallback_answer_for(message), False

    for key in keys:
        try:
            answer = _call_gemini(
                message=message,
                api_key=key,
                prompt_guardrail=prompt_guardrail,
            )
            if answer.startswith(OUT_OF_SCOPE_MARKER):
                return _out_of_scope_answer_for(message), True
            unsupported_answer = _unsupported_feature_answer_for(message, answer)
            if unsupported_answer is not None:
                return _normalize_elder_friendly_answer(unsupported_answer, _detect_language(message)), False
            return _normalize_elder_friendly_answer(answer, _detect_language(message)), False
        except Exception as exc:  # Keep endpoint resilient for UI demo flow.
            last_error = exc
            if GeminiKeyPool._is_rate_limit_error(exc):
                rate_limit_errors += 1
                GEMINI_KEY_POOL.mark_exhausted_today(key)
            continue

    if rate_limit_errors == len(keys):
        return _quota_exhausted_answer_for(message), False
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
        )

    prompt_guardrail = settings.ai_guardrail_enabled and mode in {"hybrid", "prompt_only"}
    answer, model_out_of_scope = _generate_answer_with_fallback(
        payload.message,
        prompt_guardrail=prompt_guardrail,
    )
    if settings.ai_guardrail_enabled and model_out_of_scope:
        return AIMessageResponse(
            conversation_id=conversation_id,
            in_scope=False,
            answer=answer,
        )

    return AIMessageResponse(
        conversation_id=conversation_id,
        in_scope=rules_in_scope if settings.ai_guardrail_enabled and mode == "rules_only" else True,
        answer=answer,
    )
