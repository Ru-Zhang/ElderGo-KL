"""Match chat quick-question phrasing and return deterministic guide answers."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.schemas.ai import ChatAction, ChatBlock
from app.services.ai_topic_inference_service import GuideIntent, guide_action_for_intent
from app.services.chat_blocks_service import append_official_sources, blocks_for_guide, blocks_to_plain_text

QuickQuestionId = Literal[
    "plan_route",
    "station_info",
    "weather",
    "ticket_guide",
    "concession_guide",
    "privacy",
    "preference",
]

GUIDE_QUICK_IDS: frozenset[QuickQuestionId] = frozenset(
    {"ticket_guide", "concession_guide", "privacy", "preference"}
)

FLOW_QUICK_IDS: frozenset[QuickQuestionId] = frozenset(
    {"plan_route", "station_info", "weather"}
)


@dataclass(frozen=True)
class QuickQuestionMatch:
    question_id: QuickQuestionId
    match_kind: Literal["exact", "alias"]


def _normalize_quick_text(message: str) -> str:
    text = unicodedata.normalize("NFKC", message).lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Canonical chip messages (aligned with frontend chatSuggest_*Msg).
_QUICK_CANONICAL: dict[QuickQuestionId, tuple[str, ...]] = {
    "plan_route": (
        "i want to plan a route",
        "saya mahu merancang laluan",
        "我想规划一条路线",
    ),
    "station_info": (
        "tell me about a station",
        "beritahu saya tentang stesen",
        "查询站点信息",
    ),
    "weather": (
        "check the weather",
        "semak cuaca",
        "查询天气",
    ),
    "ticket_guide": (
        "how do i buy train tickets",
        "bagaimana saya beli tiket kereta api",
        "如何购买火车票",
    ),
    "concession_guide": (
        "how do i apply for senior concession",
        "bagaimana saya memohon konsesi warga emas",
        "如何申请长者优惠",
    ),
    "privacy": (
        "how does eldergo protect my privacy",
        "bagaimana eldergo melindungi privasi saya",
        "eldergo 如何保护我的隐私",
    ),
    "preference": (
        "how do i set my travel preferences",
        "bagaimana saya tetapkan keutamaan perjalanan",
        "如何设置出行偏好",
    ),
}

# Informal aliases that should map to the same guide answer as a quick chip.
_GUIDE_ALIASES: dict[GuideIntent, tuple[str, ...]] = {
    "ticket_guide": (
        "how to buy mrt ticket",
        "how to buy lrt ticket",
        "touch n go ticket",
        "cara beli tiket",
        "怎么买票",
    ),
    "concession_guide": (
        "senior discount",
        "warga emas discount",
        "长者优惠",
        "老人票优惠",
    ),
    "privacy": (
        "privacy policy",
        "data protection",
        "个人数据",
        "隐私政策",
    ),
    "preference": (
        "travel preference",
        "accessibility first",
        "set preferences",
        "出行偏好",
    ),
}


def match_quick_question(message: str) -> QuickQuestionMatch | None:
    """Return a quick-question id when the user message matches a chip (exact or guide alias)."""
    normalized = _normalize_quick_text(message)
    if not normalized:
        return None

    for qid, phrases in _QUICK_CANONICAL.items():
        for phrase in phrases:
            if normalized == _normalize_quick_text(phrase):
                return QuickQuestionMatch(question_id=qid, match_kind="exact")

    for guide_id, aliases in _GUIDE_ALIASES.items():
        for phrase in aliases:
            if normalized == _normalize_quick_text(phrase):
                return QuickQuestionMatch(question_id=guide_id, match_kind="alias")

    return None


def resolve_quick_guide_answer(
    guide_intent: GuideIntent, language: str
) -> tuple[str, list[ChatBlock], list[ChatAction]]:
    """Return the same structured answer as resolve_intent for a guide topic (no Gemini)."""
    guide_blocks = blocks_for_guide(guide_intent, language)
    source_ctx = {"ticket_guide": "ticket", "concession_guide": "concession"}.get(guide_intent)
    if source_ctx and not any(block.type == "sources" for block in guide_blocks):
        guide_blocks = append_official_sources(guide_blocks, source_ctx, language)
    actions = [guide_action_for_intent(guide_intent)]
    return blocks_to_plain_text(guide_blocks), guide_blocks, actions


def is_flow_quick_question(question_id: QuickQuestionId) -> bool:
    return question_id in FLOW_QUICK_IDS
