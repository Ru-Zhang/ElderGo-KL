import re
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException

from app.schemas.ai import AIMessageRequest, ChatAction, ChatBlock
from app.services.chat_blocks_service import (
    blocks_for_guide,
    blocks_from_plain_text,
    blocks_in_scope_help,
    blocks_out_of_scope,
    blocks_outside_kv,
    blocks_planning_intro,
    blocks_to_plain_text,
)
from app.schemas.weather import WeatherForecastRequest
from app.services.ai_guardrail_service import is_travel_related
from app.services.klang_valley_service import place_detail_in_kv, reject_outside_kv_message
from app.services.places_service import search_places_kv
from app.services.weather_service import get_weather_forecast

IntentType = Literal[
    "out_of_scope",
    "weather",
    "route_planning",
    "ticket_guide",
    "concession_guide",
    "privacy",
    "preference",
    "route_view",
    "station_info",
    "planning",
    "general",
]

ROUTE_FROM_TO_PATTERNS = (
    re.compile(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\bgo\s+from\s+(.+?)\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"从\s*(.+?)\s*到\s*([^中途?，。、]+?)(?:\s*中途|\?|$|，|。| and )"),
    re.compile(r"dari\s+(.+?)\s+ke\s+(.+?)(?:\?|$|,|\.| and )", re.I),
)
ROUTE_FROM_ONLY = (
    re.compile(r"\bfrom\s+(.+?)(?:\?|$|,|\.|\s+to\s)", re.I),
    re.compile(r"从\s*(.+?)(?:\?|$|，|。|\s*到)"),
    re.compile(r"dari\s+(.+?)(?:\?|$|,|\.|\s+ke\s)", re.I),
)
ROUTE_GO_TO_ONLY = (
    re.compile(r"\bgo\s+to\s+(.+?)(?:\?|$|,|\.| and )", re.I),
    re.compile(r"\bke\s+(.+?)(?:\?|$|,|\.| and )", re.I),
)

WEATHER_PATTERNS = (
    re.compile(r"\b(?:weather|forecast|temperature|rain|raining|umbrella|storm|hot)\b", re.I),
    re.compile(r"\b(?:cuaca|hujan|panas|ribut)\b", re.I),
    re.compile(r"(?:天气|下雨|气温|预报)"),
)
TICKET_PATTERNS = (
    re.compile(r"\b(?:buy|purchase|get|how to buy)\s+(?:a\s+)?tickets?\b", re.I),
    re.compile(r"\bhow\s+(?:do\s+i|to)\s+.{0,40}\b(?:buy|purchase)\b.*\btickets?\b", re.I),
    re.compile(r"\b(?:buy|purchase)\b.{0,30}\btickets?\b", re.I),
    re.compile(r"\bticket\s+(?:guide|buying|machine)\b", re.I),
    re.compile(r"\b(?:touch\s*'?n\s*go|tng)\b", re.I),
    re.compile(r"(?:怎么|如何).*(?:买票|购票)"),
    re.compile(r"\bbeli\s+tiket\b", re.I),
    re.compile(r"\bpanduan\s+tiket\b", re.I),
)
CONCESSION_PATTERNS = (
    re.compile(r"\b(?:senior|elderly|warga emas)\s+(?:concession|discount)\b", re.I),
    re.compile(r"\b(?:apply|application)\b.*\b(?:concession|discount)\b", re.I),
    re.compile(r"\bconcession\b", re.I),
    re.compile(r"\bkonsesi\b", re.I),
    re.compile(r"\b(?:discount|discounts|cheaper\s+fare|half\s+fare|reduced\s+fare)\b", re.I),
    re.compile(r"\b(?:diskaun|tambang\s+murah)\b", re.I),
    re.compile(r"(?:长者|老人|乐龄).*(?:优惠|折扣)"),
    re.compile(r"(?:优惠|折扣).*(?:票|交通|地铁|公交)"),
)
PRIVACY_PATTERNS = (
    re.compile(r"\bprivacy\b", re.I),
    re.compile(r"\b(?:data protection|pdpa)\b", re.I),
    re.compile(r"\bprivasi\b", re.I),
    re.compile(r"(?:隐私|个人数据)"),
)
PREFERENCE_PATTERNS = (
    re.compile(r"\b(?:preference|preferences|travel preference)\b", re.I),
    re.compile(r"\b(?:accessibility first|least walk|fewest transfer)\b", re.I),
    re.compile(r"\bkeutamaan\b", re.I),
    re.compile(r"(?:偏好|无障碍优先|少走路)"),
)
ROUTE_VIEW_PATTERNS = (
    re.compile(r"\b(?:view|show|see|open)\s+(?:my\s+)?(?:route|trip|journey)\b", re.I),
    re.compile(r"\b(?:route|trip)\s+(?:details?|steps?|map)\b", re.I),
    re.compile(r"\b(?:text|map)\s+view\b", re.I),
    re.compile(r"\blihat\s+laluan\b", re.I),
    re.compile(r"(?:查看|我的).*(?:路线|行程)"),
)
STATION_PATTERNS = (
    re.compile(r"\b(?:station|stesen)\s+(?:info|detail|accessibility|facilit)\b", re.I),
    re.compile(r"\b(?:which|what)\s+station\b", re.I),
    re.compile(r"\b(?:lift|ramp|wheelchair)\s+at\b", re.I),
    re.compile(r"(?:站点|车站).*(?:信息|详情|无障碍)"),
)
PLANNING_PATTERNS = (
    re.compile(r"\b(?:plan|planning)\s+(?:a\s+)?route\b", re.I),
    re.compile(r"\bhow\s+(?:do\s+i|to)\s+plan\b", re.I),
    re.compile(r"\brancang\s+laluan\b", re.I),
    re.compile(r"(?:规划|路线规划)"),
)

ROUTE_MISSING_DESTINATION = {
    "en": "I have your start point as {origin}.\nWhere would you like to go?",
    "ms": "Titik mula anda ialah {origin}.\nKe mana anda mahu pergi?",
    "zh": "我已记下出发地：{origin}。\n请问您要去哪里？",
}
ROUTE_MISSING_ORIGIN = {
    "en": "I see you want to go to {destination}.\nWhere will you start from?",
    "ms": "Anda mahu pergi ke {destination}.\nDari mana anda akan bermula?",
    "zh": "我看到您要去 {destination}。\n请问您从哪里出发？",
}
ROUTE_READY_TEMPLATES = {
    "en": (
        "I can open route planning with your places filled in.\n"
        "- Start: {origin}\n"
        "- Destination: {destination}\n"
        "Please confirm each place from the list, then tap Search."
    ),
    "ms": (
        "Saya boleh buka perancangan laluan dengan tempat anda sudah diisi.\n"
        "- Mula: {origin}\n"
        "- Destinasi: {destination}\n"
        "Sila sahkan setiap tempat dari senarai, kemudian tekan Cari."
    ),
    "zh": (
        "我可以打开路线规划并填入您的地点。\n"
        "- 出发：{origin}\n"
        "- 目的地：{destination}\n"
        "请从列表中确认每个地点，然后点击搜索。"
    ),
}

KL_LOCATION_ALIASES = {
    "kl": "Kuala Lumpur",
    "klcc": "KLCC",
    "kl sentral": "KL Sentral",
    "pasar seni": "Pasar Seni",
    "bukit bintang": "Bukit Bintang",
    "ampang park": "Ampang Park",
    "titiwangsa": "Titiwangsa",
    "gombak": "Gombak",
    "putra heights": "Putra Heights",
    "subang jaya": "Subang Jaya",
    "petaling jaya": "Petaling Jaya",
    "cheras": "Cheras",
    "wangsa maju": "Wangsa Maju",
    "bandar utama": "Bandar Utama",
}

OUT_OF_SCOPE_TEMPLATES = {
    "zh": (
        "我目前只能协助巴生谷（Klang Valley）内的出行问题，例如路线、站点、天气、票务指南、优惠与 App 使用。\n"
        "请把问题改成以上主题，我会一步一步协助你。"
    ),
    "ms": (
        "Saya hanya boleh bantu perjalanan dalam Lembah Klang: laluan, stesen, cuaca, panduan tiket, konsesi, dan penggunaan app.\n"
        "Tanya tentang salah satu topik ini, dan saya akan bantu langkah demi langkah."
    ),
    "en": (
        "I can only help with travel in the Klang Valley: routes, stations, weather, ticket guides, concessions, and how to use ElderGo KL.\n"
        "Ask about one of these topics, and I will guide you step by step."
    ),
}

GUIDE_ANSWERS = {
    "ticket_guide": {
        "en": (
            "ElderGo KL shows ticket-buying steps only; it cannot sell tickets or take payment in the app.\n"
            "- Open the ticket guide in Help for simple steps.\n"
            "- Buy tickets at station machines, counters, or use a Touch 'n Go card.\n"
            "You can open the ticket guide now to read the steps before you travel."
        ),
        "ms": (
            "ElderGo KL hanya menunjukkan langkah membeli tiket; ia tidak menjual tiket dalam app.\n"
            "- Buka panduan tiket di Help.\n"
            "- Beli tiket di mesin, kaunter, atau gunakan kad Touch 'n Go.\n"
            "Anda boleh buka panduan tiket sekarang sebelum bergerak."
        ),
        "zh": (
            "ElderGo KL 只提供买票指南，不能在 App 内买票或付款。\n"
            "- 在 Help 页面查看买票步骤。\n"
            "- 实际买票请使用售票机、柜台或 Touch 'n Go 卡。\n"
            "你可以现在打开买票指南，出发前先看一遍。"
        ),
    },
    "concession_guide": {
        "en": (
            "ElderGo KL provides senior concession information only; it cannot submit an application in the app.\n"
            "- Open the concession guide in Help to see what to prepare.\n"
            "- Apply at the counter or official channel shown in the guide.\n"
            "You can open the concession guide now and prepare your MyKad."
        ),
        "ms": (
            "ElderGo KL hanya menyediakan maklumat konsesi warga emas; ia tidak boleh menghantar permohonan dalam app.\n"
            "- Buka panduan konsesi di Help.\n"
            "- Mohon melalui kaunter atau saluran rasmi dalam panduan.\n"
            "Anda boleh buka panduan konsesi sekarang dan sediakan MyKad."
        ),
        "zh": (
            "ElderGo KL 只提供长者优惠申请信息，不能在 App 内提交申请。\n"
            "- 在 Help 页面查看需要准备的文件和步骤。\n"
            "- 请按指南到柜台或官方渠道办理。\n"
            "你可以现在打开优惠指南并准备好 MyKad。"
        ),
    },
    "privacy": {
        "en": (
            "ElderGo KL protects your privacy: no GPS tracking, no saved travel history, and no ads.\n"
            "- Open Privacy in Help to read the full promise.\n"
            "- Your route details stay on your phone unless you choose to share them.\n"
            "You can open the privacy page now for a short, clear summary."
        ),
        "ms": (
            "ElderGo KL melindungi privasi anda: tiada penjejakan GPS, tiada sejarah perjalanan disimpan, tiada iklan.\n"
            "- Buka Privasi di Help untuk baca janji penuh.\n"
            "- Butiran laluan kekal di telefon anda melainkan anda kongsi.\n"
            "Anda boleh buka halaman privasi sekarang."
        ),
        "zh": (
            "ElderGo KL 保护您的隐私：不追踪 GPS、不保存出行记录、无广告。\n"
            "- 在 Help 中打开隐私说明查看完整承诺。\n"
            "- 路线信息保存在您的手机上，除非您主动分享。\n"
            "你可以现在打开隐私页面阅读简要说明。"
        ),
    },
    "preference": {
        "en": (
            "You can set travel preferences in ElderGo KL to match your needs.\n"
            "- Turn on Accessibility first for lifts and step-free paths.\n"
            "- Choose Least walk or Fewest transfers if those matter more.\n"
            "You can open Preferences now and save what feels comfortable."
        ),
        "ms": (
            "Anda boleh tetapkan keutamaan perjalanan dalam ElderGo KL.\n"
            "- Hidupkan Utamakan aksesibiliti untuk lif dan laluan tanpa tangga.\n"
            "- Pilih Kurang berjalan atau Kurang pertukaran jika perlu.\n"
            "Anda boleh buka Keutamaan sekarang dan simpan tetapan anda."
        ),
        "zh": (
            "您可以在 ElderGo KL 中设置出行偏好。\n"
            "- 开启「无障碍优先」以偏好电梯和无台阶路径。\n"
            "- 也可选择少走路或少换乘。\n"
            "你可以现在打开偏好设置并保存。"
        ),
    },
}


@dataclass
class IntentResult:
    intent: IntentType | str
    answer: str | None = None
    answer_blocks: list[ChatBlock] | None = None
    actions: list[ChatAction] | None = None
    in_scope: bool = True
    chat_flow: str | None = None
    flow_slots: dict[str, str] | None = None
    response_source: str | None = None


def detect_language(message: str) -> str:
    if any("\u4e00" <= ch <= "\u9fff" for ch in message):
        return "zh"
    lowered = message.lower()
    malay_hints = (" saya ", " dan ", " bagaimana ", " stesen ", " laluan ", " tiket ", " boleh ", " cuaca ")
    padded = f" {lowered} "
    if any(hint in padded for hint in malay_hints):
        return "ms"
    return "en"


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


_PLACE_TIME_TAIL_PATTERNS = (
    re.compile(r"\s+at\s+the\s+(?:evening|morning|afternoon|night)\b.*$", re.I),
    re.compile(r"\s+in\s+the\s+(?:evening|morning|afternoon)\b.*$", re.I),
    re.compile(r"\s+(?:this|tomorrow)\s+(?:evening|morning|afternoon|night)\b.*$", re.I),
    re.compile(r"\s+(?:tonight|today)\b.*$", re.I),
    re.compile(r"\s+(?:晚上|早上|下午|傍晚|中午).*$"),
    re.compile(r"\s*,\s*(?:could|can|would|please|thank|recommend).*$", re.I),
)


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


def _has_route_planning_signal(message: str, origin: str | None, destination: str | None) -> bool:
    if origin and destination:
        return True
    if origin and re.search(r"\b(?:from|dari)\s+", message, re.I):
        return True
    if destination and re.search(
        r"\b(?:go\s+to|wanna|want\s+to|heading\s+to|get\s+to|ke)\s+", message, re.I
    ):
        return True
    return False


def extract_route_endpoints(message: str) -> tuple[str | None, str | None]:
    from app.services.ai_route_sentence_service import extract_route_endpoints as parse_endpoints

    return parse_endpoints(message)


def build_planning_prefill_action(origin: str, destination: str) -> ChatAction:
    return ChatAction(
        type="open_planning",
        origin_name=origin,
        destination_name=destination,
    )


def extract_weather_location(message: str, request: AIMessageRequest) -> str:
    if request.destination_name:
        return request.destination_name.strip()
    if request.origin_name:
        return request.origin_name.strip()

    lowered = message.lower()
    for alias, canonical in sorted(KL_LOCATION_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in lowered:
            return canonical

    at_match = re.search(
        r"(?:at|in|for|near|de|di|ke|到|在)\s+([A-Za-z0-9][A-Za-z0-9\s.'-]{1,40})",
        message,
        re.I,
    )
    if at_match:
        candidate = at_match.group(1).strip(" .,!?:;")
        for stop in (" now", " today", " tomorrow", " sekarang", " hari ini"):
            if candidate.lower().endswith(stop):
                candidate = candidate[: -len(stop)].strip()
        if len(candidate) >= 2:
            return candidate

    return ""


def classify_intent(message: str, request: AIMessageRequest) -> IntentType:
    if not is_travel_related(message):
        return "out_of_scope"

    if _matches_any(message, WEATHER_PATTERNS):
        return "weather"

    if _matches_any(message, TICKET_PATTERNS):
        return "ticket_guide"
    if _matches_any(message, CONCESSION_PATTERNS):
        return "concession_guide"
    if _matches_any(message, PRIVACY_PATTERNS):
        return "privacy"
    if _matches_any(message, PREFERENCE_PATTERNS):
        return "preference"

    origin, destination = extract_route_endpoints(message)
    if _has_route_planning_signal(message, origin, destination):
        return "route_planning"
    if _matches_any(message, ROUTE_VIEW_PATTERNS):
        return "route_view"
    if _matches_any(message, STATION_PATTERNS):
        return "station_info"
    if _matches_any(message, PLANNING_PATTERNS):
        return "planning"

    return "general"


def _format_weather_answer(forecast, language: str) -> str:
    from app.services.ai_flow_service import format_weather_report

    return format_weather_report(forecast, language)


IN_SCOPE_HELP = {
    "en": (
        "I can help with Klang Valley travel in ElderGo KL.\n"
        "- Plan a route or ask for start and destination.\n"
        "- Check weather for a place in Klang Valley.\n"
        "- Look up station accessibility and facilities.\n"
        "- Open ticket, concession, privacy, or preference guides in the app.\n"
        "Try a quick question below, or tell me what you need."
    ),
    "ms": (
        "Saya boleh bantu perjalanan Lembah Klang dalam ElderGo KL.\n"
        "- Rancang laluan atau beritahu titik mula dan destinasi.\n"
        "- Semak cuaca untuk tempat dalam Lembah Klang.\n"
        "- Lihat kebolehcapaian dan kemudahan stesen.\n"
        "- Buka panduan tiket, konsesi, privasi, atau keutamaan dalam app.\n"
        "Cuba soalan pantas di bawah, atau beritahu apa yang anda perlukan."
    ),
    "zh": (
        "我可以协助您在 ElderGo KL 中进行巴生谷出行。\n"
        "- 规划路线或告诉我出发地和目的地。\n"
        "- 查询巴生谷内某地的天气。\n"
        "- 查看站点无障碍与设施信息。\n"
        "- 在 App 内打开票务、优惠、隐私或偏好指南。\n"
        "请使用下方快捷问题，或告诉我您的需求。"
    ),
}


async def resolve_intent(message: str, request: AIMessageRequest) -> IntentResult | None:
    from app.services.ai_language import resolve_response_language

    intent = classify_intent(message, request)
    language = resolve_response_language(request, message)

    if intent == "out_of_scope":
        scope_blocks = blocks_out_of_scope(language)
        return IntentResult(
            intent=intent,
            answer=blocks_to_plain_text(scope_blocks),
            answer_blocks=scope_blocks,
            actions=[],
            in_scope=False,
        )

    if intent == "route_planning":
        from app.services.ai_route_parse_service import normalize_place_query
        from app.services.ai_route_sentence_service import parse_route_sentence

        parsed = parse_route_sentence(message)
        origin, destination = parsed.origin, parsed.destination
        departure = parsed.departure or "now"
        if origin and destination:
            origin_places = await search_places_kv(normalize_place_query(origin), limit=1)
            dest_places = await search_places_kv(normalize_place_query(destination), limit=1)
            origin_ok = origin_places and place_detail_in_kv(origin_places[0])
            dest_ok = dest_places and place_detail_in_kv(dest_places[0])
            if not origin_ok or not dest_ok:
                outside_blocks = blocks_outside_kv(language)
                return IntentResult(
                    intent=intent,
                    answer=blocks_to_plain_text(outside_blocks),
                    answer_blocks=outside_blocks,
                    actions=[],
                    in_scope=True,
                )
            o_place = origin_places[0]
            d_place = dest_places[0]
            ready = {
                "en": (
                    f"Your route from {o_place.display_name} to {d_place.display_name} is ready.\n"
                    "Opening your recommended route now."
                ),
                "ms": (
                    f"Laluan dari {o_place.display_name} ke {d_place.display_name} sudah siap.\n"
                    "Membuka laluan cadangan anda sekarang."
                ),
                "zh": (
                    f"从 {o_place.display_name} 到 {d_place.display_name} 的路线已准备好。\n"
                    "正在为您打开推荐路线。"
                ),
            }
            return IntentResult(
                intent=intent,
                answer=ready[language],
                actions=[
                    ChatAction(
                        type="compute_route",
                        origin_name=o_place.display_name,
                        destination_name=d_place.display_name,
                        departure_time=departure,
                        origin_lat=o_place.lat,
                        origin_lon=o_place.lon,
                        origin_google_place_id=o_place.google_place_id,
                        destination_lat=d_place.lat,
                        destination_lon=d_place.lon,
                        destination_google_place_id=d_place.google_place_id,
                    )
                ],
                in_scope=True,
            )
        if origin and not destination:
            from app.services.ai_flow_service import enter_plan_route_partial

            return await enter_plan_route_partial(
                message,
                origin=origin,
                destination=None,
                departure=parsed.departure,
                language=language,
            )
        if destination and not origin:
            from app.services.ai_flow_service import enter_plan_route_partial

            return await enter_plan_route_partial(
                message,
                origin=None,
                destination=destination,
                departure=parsed.departure,
                language=language,
            )

    if intent == "weather":
        from app.services.ai_flow_service import resolve_chat_flow

        flow_result = await resolve_chat_flow(message, request)
        if flow_result is not None:
            return flow_result

    if intent in {"ticket_guide", "concession_guide", "privacy", "preference"}:
        from app.services.ai_topic_inference_service import (
            blocks_inferred_topic_answer,
            guide_action_for_intent,
            infer_probable_guide_intent,
        )

        from app.services.chat_blocks_service import append_official_sources

        guide_intent = intent  # type: ignore[assignment]
        probable = infer_probable_guide_intent(message)
        guide_source_context = {
            "ticket_guide": "ticket",
            "concession_guide": "concession",
        }
        if probable == guide_intent:
            guide_blocks = blocks_inferred_topic_answer(guide_intent, language)
        else:
            guide_blocks = blocks_for_guide(guide_intent, language)
        ctx = guide_source_context.get(guide_intent)
        if ctx and not any(block.type == "sources" for block in guide_blocks):
            guide_blocks = append_official_sources(guide_blocks, ctx, language)
        return IntentResult(
            intent=intent,
            answer=blocks_to_plain_text(guide_blocks),
            answer_blocks=guide_blocks,
            actions=[guide_action_for_intent(guide_intent)],
            in_scope=True,
        )

    if intent == "route_view":
        if request.has_current_route:
            return IntentResult(
                intent=intent,
                answer={
                    "en": (
                        "Your planned route is ready in ElderGo KL.\n"
                        "- Text view shows step-by-step instructions.\n"
                        "- Map view shows the path on a map.\n"
                        "You can open your route now."
                    ),
                    "ms": (
                        "Laluan anda sudah tersedia dalam ElderGo KL.\n"
                        "- Paparan teks menunjukkan langkah demi langkah.\n"
                        "- Paparan peta menunjukkan laluan pada peta.\n"
                        "Anda boleh buka laluan sekarang."
                    ),
                    "zh": (
                        "您的路线已在 ElderGo KL 中准备好。\n"
                        "- 文字视图显示逐步指引。\n"
                        "- 地图视图显示路线地图。\n"
                        "你现在可以打开路线。"
                    ),
                }[language],
                actions=[
                    ChatAction(type="open_route_text"),
                    ChatAction(type="open_route_map"),
                ],
                in_scope=True,
            )
        return IntentResult(
            intent=intent,
            answer={
                "en": (
                    "You do not have a planned route yet.\n"
                    "- Enter your start point and destination on the Planning page.\n"
                    "- ElderGo KL will show one recommended route.\n"
                    "You can open Planning now to start."
                ),
                "ms": (
                    "Anda belum mempunyai laluan dirancang.\n"
                    "- Masukkan titik mula dan destinasi di halaman Perancangan.\n"
                    "- ElderGo KL akan tunjukkan satu laluan cadangan.\n"
                    "Anda boleh buka Perancangan sekarang."
                ),
                "zh": (
                    "您还没有规划好的路线。\n"
                    "- 在规划页输入出发地和目的地。\n"
                    "- ElderGo KL 会显示一条推荐路线。\n"
                    "你现在可以打开规划页面开始。"
                ),
            }[language],
            actions=[ChatAction(type="open_planning")],
            in_scope=True,
        )

    if intent == "station_info":
        if request.selected_station_id:
            return IntentResult(
                intent=intent,
                answer={
                    "en": (
                        f"Station details for {request.selected_station_name or 'your station'} are available.\n"
                        "- See accessibility, facilities, and opening hours.\n"
                        "- You can start a route from this station too.\n"
                        "Open the station page now."
                    ),
                    "ms": (
                        f"Butiran stesen untuk {request.selected_station_name or 'stesen anda'} tersedia.\n"
                        "- Lihat kebolehcapaian, kemudahan, dan waktu operasi.\n"
                        "- Anda juga boleh mulakan laluan dari stesen ini.\n"
                        "Buka halaman stesen sekarang."
                    ),
                    "zh": (
                        f"{request.selected_station_name or '站点'} 的详情可以查看。\n"
                        "- 包括无障碍、设施和营业时间。\n"
                        "- 也可以从此站开始规划路线。\n"
                        "你现在可以打开站点页面。"
                    ),
                }[language],
                actions=[
                    ChatAction(
                        type="open_station_detail",
                        station_id=request.selected_station_id,
                    )
                ],
                in_scope=True,
            )
        from app.services.ai_flow_service import ASK_STATION

        return IntentResult(
            intent=intent,
            answer=ASK_STATION[language],
            actions=[],
            in_scope=True,
            chat_flow="station_info",
            flow_slots={},
        )

    if intent == "planning":
        intro_blocks = blocks_planning_intro(language)
        return IntentResult(
            intent=intent,
            answer=blocks_to_plain_text(intro_blocks),
            answer_blocks=intro_blocks,
            actions=[ChatAction(type="open_planning")],
            in_scope=True,
        )

    return None


def should_use_gemini_supplement(message: str) -> bool:
    """Use Gemini only for substantive in-scope questions not covered by app features."""
    from app.services.ai_exploratory_poi_service import is_exploratory_poi_message
    from app.services.ai_topic_inference_service import infer_probable_guide_intent

    if is_exploratory_poi_message(message):
        return True

    if infer_probable_guide_intent(message) is None and classify_intent(message, AIMessageRequest(message=message)) == "general":
        stripped = message.strip()
        if len(stripped) >= 8:
            return True

    stripped = message.strip()
    cjk_count = sum(1 for ch in stripped if "\u4e00" <= ch <= "\u9fff")
    min_len = 12 if cjk_count >= 4 else 24
    if len(stripped) < min_len:
        return False
    lowered = stripped.lower()
    vague_prefixes = (
        "hi",
        "hello",
        "hey",
        "help",
        "thanks",
        "thank you",
        "what can you do",
        "what can you help",
        "who are you",
    )
    return not any(lowered.startswith(prefix) for prefix in vague_prefixes)
