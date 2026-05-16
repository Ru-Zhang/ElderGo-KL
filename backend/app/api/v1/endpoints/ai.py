import re
from uuid import uuid4

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.ai import (
    AIConversationResponse,
    AIMessageRequest,
    AIMessageResponse,
    ChatAction,
    ChatBlock,
    ResponseSourceType,
)
from app.services.ai_exploratory_poi_service import (
    extract_poi_category_term,
    is_enroute_rest_exploratory,
    is_exploratory_poi_message,
    is_senior_common_poi_message,
    resolve_exploratory_poi,
    should_prefer_gemini_recommendation,
)
from app.services.ai_route_parse_service import message_has_plan_route_endpoints
from app.services.ai_grounding_service import build_grounded_context
from app.services.chat_blocks_service import (
    blocks_from_plain_text,
    blocks_in_scope_help,
    blocks_maps_grounding_places,
    blocks_out_of_scope,
    blocks_to_plain_text,
    parse_gemini_blocks_json,
)
from app.services.ai_guardrail_service import is_travel_related
from app.services.ai_topic_inference_service import (
    blocks_inferred_topic_answer,
    guide_action_for_intent,
    infer_probable_guide_intent,
)
from app.services.ai_flow_service import resolve_chat_flow
from app.services.ai_language import resolve_response_language
from app.services.ai_intent_service import (
    IN_SCOPE_HELP,
    build_planning_prefill_action,
    classify_intent,
    extract_route_endpoints,
    resolve_intent,
    should_use_gemini_supplement,
)
from app.services.gemini_client import (
    GEMINI_KEY_POOL,
    MAPS_GROUNDING_LANGUAGE,
    GeminiKeyPool,
    call_with_key_pool,
    extract_grounding_places,
    extract_text_from_response,
)

router = APIRouter()
settings = get_settings()

GUIDE_INTENTS = frozenset({"ticket_guide", "concession_guide", "privacy", "preference"})


def _guide_actions_for_message(message: str, request: AIMessageRequest) -> list[ChatAction]:
    intent = classify_intent(message, request)
    action_map = {
        "ticket_guide": ChatAction(type="open_ticket_guide"),
        "concession_guide": ChatAction(type="open_concession_guide"),
        "privacy": ChatAction(type="open_privacy"),
        "preference": ChatAction(type="open_preference"),
    }
    action = action_map.get(intent)
    return [action] if action else []

OUT_OF_SCOPE_MARKER = "[OUT_OF_SCOPE]"
MAPS_GROUNDING_SUPPLEMENT = (
    "Use Google Maps data for the Klang Valley (Kuala Lumpur area) only. "
    "Keep the answer short (at most 4 sentences) and practical for older adults."
)
SENIOR_POI_GEMINI_SUPPLEMENT = (
    "The user is asking for a real place recommendation (for example hospital, clinic, pharmacy, mall, or market). "
    "Name 2-3 specific venues near the anchor they mentioned, with area names seniors recognise. "
    "Prefer hospitals/clinics for medical questions — do not suggest cafes, student lounges, or unrelated shops. "
    "Mention which is nearest or easiest by public transport when you can. "
    "If you are unsure, say so briefly instead of guessing."
)
SUPPORTED_GUARDRAIL_MODES = {"hybrid", "rules_only", "prompt_only"}

GUARDRAIL_PROMPT = (
    "You are ElderGo KL assistant for the Klang Valley only. Only answer ElderGo KL transport support topics: routes, stations, "
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
GEMINI_JSON_PROMPT = (
    "Return ONLY valid JSON (no markdown fences) in this shape:\n"
    '{"blocks":[{"type":"heading","text":"..."},{"type":"paragraph","text":"..."},'
    '{"type":"bullets","items":["..."]},{"type":"callout","tone":"info","text":"..."},'
    '{"type":"sources","links":[{"title":"...","url":"...","org":"..."}]}]}\n'
    "Use at most 1 heading, 1 short paragraph, 2-4 bullet items, optional 1 callout "
    "(tone: info, warning, or success), and optional sources.\n"
    "Sources URLs must be ONLY from this allowlist:\n"
    "- https://myrapid.com.my/\n"
    "- https://www.mrt.com.my/\n"
    "- https://openweathermap.org/\n"
    "Explain acronyms simply (LRT, MRT, BRT, Touch 'n Go). Keep total content short."
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
        "我目前只能协助巴生谷出行相关的问题，例如路线、站点、天气、票务指南、优惠信息与 App 使用。\n"
        "请把问题改成以上主题，我会一步一步协助你。"
    ),
    "ms": (
        "Saya hanya boleh bantu perjalanan di Klang Valley: laluan, stesen, cuaca, panduan tiket, konsesi, dan penggunaan app.\n"
        "Tanya tentang salah satu topik ini, dan saya akan bantu langkah demi langkah."
    ),
    "en": (
        "I can only help with travel in Klang Valley: routes, stations, weather, ticket guides, concessions, and how to use ElderGo KL.\n"
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
    re.compile(
        r"\b(?:buy|purchase|get)\s+(?:a\s+)?tickets?\s+(?:in|inside|through|from|using|with)\s+(?:the\s+|this\s+)?(?:app|eldergo)",
        re.I,
    ),
    re.compile(r"\b(?:you\s+can\s+)?buy\s+tickets?\s+in\s+this\s+app\b", re.I),
    re.compile(r"\b(?:the\s+)?(?:app|eldergo)\s+(?:can|lets you|allows you to)\s+(?:buy|purchase|get)\s+(?:a\s+)?tickets?", re.I),
    re.compile(
        r"\b(?:pay|top up|reload|buy tokens?)\s+(?:in|inside|through|from|using|with)\s+(?:the\s+|this\s+)?(?:app|eldergo)",
        re.I,
    ),
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


def _response_language(payload: AIMessageRequest) -> str:
    return resolve_response_language(payload, payload.message)


def _out_of_scope_answer_for(payload: AIMessageRequest) -> str:
    return OUT_OF_SCOPE_TEMPLATES[_response_language(payload)]


def _out_of_scope_blocks_for(language: str) -> list[ChatBlock]:
    return blocks_out_of_scope(language)


def _message_response(
    conversation_id: str,
    *,
    answer: str | None = None,
    blocks: list[ChatBlock] | None = None,
    in_scope: bool = True,
    actions: list[ChatAction] | None = None,
    chat_flow=None,
    flow_slots: dict[str, str] | None = None,
    response_source: ResponseSourceType | None = None,
) -> AIMessageResponse:
    if blocks:
        resolved_blocks = list(blocks)
        resolved_answer = (answer or "").strip() or blocks_to_plain_text(resolved_blocks)
    elif answer:
        resolved_answer = answer.strip()
        resolved_blocks = blocks_from_plain_text(resolved_answer)
    else:
        resolved_answer = ""
        resolved_blocks = []
    return AIMessageResponse(
        conversation_id=conversation_id,
        answer=resolved_answer,
        answer_blocks=resolved_blocks,
        in_scope=in_scope,
        actions=actions or [],
        chat_flow=chat_flow,
        flow_slots=flow_slots or {},
        response_source=response_source,
    )


def _from_intent_result(
    conversation_id: str,
    result,
    *,
    fallback_answer: str,
) -> AIMessageResponse:
    blocks = list(result.answer_blocks or [])
    if not blocks and result.answer:
        blocks = blocks_from_plain_text(result.answer)
    answer = (result.answer or "").strip() or blocks_to_plain_text(blocks) or fallback_answer
    return _message_response(
        conversation_id,
        answer=answer,
        blocks=blocks,
        in_scope=result.in_scope,
        actions=result.actions or [],
        chat_flow=result.chat_flow,
        flow_slots=result.flow_slots or {},
        response_source=result.response_source,
    )


def _fallback_answer_for(payload: AIMessageRequest) -> str:
    return FALLBACK_TEMPLATES[_response_language(payload)]


def _quota_exhausted_answer_for(payload: AIMessageRequest) -> str:
    return QUOTA_EXHAUSTED_TEMPLATES[_response_language(payload)]


def _guardrail_mode() -> str:
    mode = (settings.ai_guardrail_mode or "hybrid").strip().lower()
    if mode not in SUPPORTED_GUARDRAIL_MODES:
        return "hybrid"
    return mode


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _unsupported_feature_answer_for(message: str, answer: str, language: str) -> str | None:
    combined = f"{message}\n{answer}"

    if _matches_any(combined, UNSUPPORTED_TICKET_PATTERNS):
        return UNSUPPORTED_TEMPLATES["ticket"][language]
    if _matches_any(combined, UNSUPPORTED_CONCESSION_PATTERNS):
        return UNSUPPORTED_TEMPLATES["concession"][language]
    if _matches_any(combined, UNSUPPORTED_STAFF_CONTACT_PATTERNS):
        return UNSUPPORTED_TEMPLATES["staff"][language]
    return None


def _build_gemini_user_prompt(
    message: str,
    *,
    prompt_guardrail: bool,
    use_maps_grounding: bool,
    grounded_facts: list[str],
    senior_poi_recommendation: bool = False,
) -> str:
    parts: list[str] = []
    if prompt_guardrail:
        parts.extend([GUARDRAIL_PROMPT, PROJECT_CAPABILITY_PROMPT])
    if grounded_facts:
        facts_block = "\n".join(f"- {fact}" for fact in grounded_facts[:8])
        parts.append(f"Verified ElderGo data (prefer when relevant):\n{facts_block}")
    if senior_poi_recommendation:
        category = extract_poi_category_term(message)
        if category:
            parts.append(f"Place type requested: {category}.")
        parts.append(SENIOR_POI_GEMINI_SUPPLEMENT)
    if use_maps_grounding:
        parts.append(MAPS_GROUNDING_SUPPLEMENT)
        parts.append(f"User message:\n{message}")
    elif prompt_guardrail:
        parts.append(GEMINI_JSON_PROMPT)
        parts.append(f"User message:\n{message}")
    else:
        parts.append(message)
    return "\n\n".join(parts)


def _should_use_maps_grounding(message: str, *, exploratory_places_failed: bool) -> bool:
    if should_prefer_gemini_recommendation(message) and should_use_gemini_supplement(message):
        return True
    return (
        exploratory_places_failed
        and is_exploratory_poi_message(message)
        and should_use_gemini_supplement(message)
    )


def _needs_gemini_poi_recommendation(message: str, *, poi_result) -> bool:
    return poi_result is None and (
        should_prefer_gemini_recommendation(message)
        or is_exploratory_poi_message(message)
        or is_enroute_rest_exploratory(message)
    )


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


async def _generate_answer_with_fallback(
    message: str,
    prompt_guardrail: bool,
    language: str,
    *,
    request: AIMessageRequest | None = None,
    use_maps_grounding: bool = False,
    senior_poi_recommendation: bool = False,
) -> tuple[str, bool, list[ChatBlock], ResponseSourceType]:
    grounded = build_grounded_context(
        message=message,
        current_route_id=None,
        selected_location_id=request.selected_station_id if request else None,
        anonymous_user_id=None,
    )
    grounded_facts = grounded.facts if grounded.grounded else []

    user_prompt = _build_gemini_user_prompt(
        message,
        prompt_guardrail=prompt_guardrail and not use_maps_grounding,
        use_maps_grounding=use_maps_grounding,
        grounded_facts=grounded_facts,
        senior_poi_recommendation=senior_poi_recommendation,
    )
    maps_lang = MAPS_GROUNDING_LANGUAGE.get(language, "en_US")
    data, error_kind = await call_with_key_pool(
        user_prompt,
        use_maps_grounding=use_maps_grounding,
        language_code=maps_lang,
        timeout=20.0 if not use_maps_grounding else 25.0,
    )

    if error_kind == "quota_exhausted":
        text = QUOTA_EXHAUSTED_TEMPLATES[language]
        return text, False, blocks_from_plain_text(text), "gemini"
    if error_kind or not data:
        text = FALLBACK_TEMPLATES[language]
        return text, False, blocks_from_plain_text(text), "gemini"

    try:
        answer = extract_text_from_response(data)
    except ValueError:
        text = FALLBACK_TEMPLATES[language]
        return text, False, blocks_from_plain_text(text), "gemini"

    source: ResponseSourceType = "gemini_maps" if use_maps_grounding else "gemini"

    if answer.startswith(OUT_OF_SCOPE_MARKER):
        text = OUT_OF_SCOPE_TEMPLATES[language]
        return text, True, blocks_out_of_scope(language), source

    if use_maps_grounding:
        places = extract_grounding_places(data, limit=3)
        summary = _normalize_elder_friendly_answer(answer, language) if answer else None
        blocks = blocks_maps_grounding_places(places, language, summary=summary)
        plain = blocks_to_plain_text(blocks)
        return plain, False, blocks, "gemini_maps"

    unsupported_answer = _unsupported_feature_answer_for(message, answer, language)
    if unsupported_answer is not None:
        normalized = _normalize_elder_friendly_answer(unsupported_answer, language)
        return normalized, False, blocks_from_plain_text(normalized), "gemini"

    parsed_blocks = parse_gemini_blocks_json(answer, language) if prompt_guardrail else None
    if parsed_blocks:
        return blocks_to_plain_text(parsed_blocks), False, parsed_blocks, "gemini"
    normalized = _normalize_elder_friendly_answer(answer, language)
    return normalized, False, blocks_from_plain_text(normalized), "gemini"


@router.post("/conversations", response_model=AIConversationResponse)
def create_conversation() -> AIConversationResponse:
    # Lightweight stateless conversation id for UI threading in demo mode.
    return AIConversationResponse(conversation_id=f"conv_{uuid4().hex[:16]}")


@router.post("/conversations/{conversation_id}/messages", response_model=AIMessageResponse)
async def send_message(conversation_id: str, payload: AIMessageRequest) -> AIMessageResponse:
    # Resolution order: guardrail → guide intents → plan_route fast-path → exploratory POI
    # → structured chat flows → DB intent → Gemini (optional Maps grounding).
    mode = _guardrail_mode()
    travel_related = is_travel_related(payload.message)
    language = _response_language(payload)

    probable_guide = infer_probable_guide_intent(payload.message)
    if probable_guide and not payload.chat_flow and not travel_related:
        clarify_blocks = blocks_inferred_topic_answer(probable_guide, language)
        return _message_response(
            conversation_id,
            blocks=clarify_blocks,
            in_scope=True,
            actions=[guide_action_for_intent(probable_guide)],
            response_source="db",
        )

    if settings.ai_guardrail_enabled and not travel_related and not payload.chat_flow:
        if mode in {"hybrid", "rules_only"} or settings.ai_guardrail_strict:
            return _message_response(
                conversation_id,
                answer=_out_of_scope_answer_for(payload),
                blocks=_out_of_scope_blocks_for(language),
                in_scope=False,
                actions=[],
                response_source="db",
            )

    classified = classify_intent(payload.message, payload)
    if classified in GUIDE_INTENTS:
        guide_result = await resolve_intent(payload.message, payload)
        if guide_result is not None:
            return _from_intent_result(
                conversation_id,
                guide_result,
                fallback_answer=_fallback_answer_for(payload),
            )

    # Route planning first — avoids Google Places round-trips on "from A to B" messages.
    if message_has_plan_route_endpoints(payload.message) or payload.chat_flow == "plan_route":
        flow_result = await resolve_chat_flow(payload.message, payload)
        if flow_result is not None:
            return _from_intent_result(
                conversation_id,
                flow_result,
                fallback_answer=_fallback_answer_for(payload),
            )

    poi_result = await resolve_exploratory_poi(payload.message, language)
    if poi_result is not None:
        return _from_intent_result(
            conversation_id,
            poi_result,
            fallback_answer=_fallback_answer_for(payload),
        )

    flow_result = await resolve_chat_flow(payload.message, payload)
    if flow_result is not None:
        return _from_intent_result(
            conversation_id,
            flow_result,
            fallback_answer=_fallback_answer_for(payload),
        )

    intent_result = await resolve_intent(payload.message, payload)
    if intent_result is not None and not is_enroute_rest_exploratory(payload.message):
        return _from_intent_result(
            conversation_id,
            intent_result,
            fallback_answer=_fallback_answer_for(payload),
        )

    exploratory_failed = _needs_gemini_poi_recommendation(payload.message, poi_result=poi_result)
    senior_poi = should_prefer_gemini_recommendation(payload.message)

    if not should_use_gemini_supplement(payload.message) and not exploratory_failed:
        help_blocks = blocks_in_scope_help(language)
        return _message_response(
            conversation_id,
            answer=IN_SCOPE_HELP[language],
            blocks=help_blocks,
            in_scope=True,
            actions=[ChatAction(type="open_help")],
            response_source="db",
        )

    prompt_guardrail = settings.ai_guardrail_enabled and mode in {"hybrid", "prompt_only"}
    use_maps = _should_use_maps_grounding(
        payload.message,
        exploratory_places_failed=exploratory_failed,
    )
    answer, model_out_of_scope, answer_blocks, gemini_source = await _generate_answer_with_fallback(
        payload.message,
        prompt_guardrail=prompt_guardrail,
        language=language,
        request=payload,
        use_maps_grounding=use_maps,
        senior_poi_recommendation=senior_poi,
    )
    if settings.ai_guardrail_enabled and model_out_of_scope:
        return _message_response(
            conversation_id,
            answer=answer,
            blocks=answer_blocks,
            in_scope=False,
            actions=[],
            response_source=gemini_source,
        )

    gemini_actions: list[ChatAction] = []
    origin, destination = extract_route_endpoints(payload.message)
    if origin and destination:
        gemini_actions = [build_planning_prefill_action(origin, destination)]
    elif payload.has_current_route:
        gemini_actions.extend(
            [
                ChatAction(type="open_route_text"),
                ChatAction(type="open_route_map"),
            ]
        )
    if not gemini_actions:
        gemini_actions = _guide_actions_for_message(payload.message, payload)

    return _message_response(
        conversation_id,
        answer=answer,
        blocks=answer_blocks,
        in_scope=travel_related if settings.ai_guardrail_enabled and mode == "rules_only" else True,
        actions=gemini_actions,
        response_source=gemini_source,
    )
