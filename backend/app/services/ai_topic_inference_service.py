"""Map vague or colloquial questions to ElderGo guide topics before refusing."""

from __future__ import annotations

import re
from typing import Literal

from app.schemas.ai import ChatAction, ChatBlock

GuideIntent = Literal["ticket_guide", "concession_guide", "privacy", "preference"]

# Ordered: more specific patterns first.
_TOPIC_RULES: tuple[tuple[GuideIntent, tuple[re.Pattern[str], ...]], ...] = (
    (
        "concession_guide",
        (
            re.compile(r"\b(?:senior|elderly|warga\s+emas)\s+(?:concession|discount|fare)\b", re.I),
            re.compile(r"\b(?:apply|application|register)\b.*\b(?:concession|discount)\b", re.I),
            re.compile(r"\b(?:concession|konsesi)\b", re.I),
            re.compile(r"\b(?:discount|discounts|cheaper\s+fare|half\s+fare|reduced\s+fare)\b", re.I),
            re.compile(r"\b(?:diskaun|tambang\s+murah|kadar\s+warga\s+emas)\b", re.I),
            re.compile(r"(?:长者|老人|乐龄|银发).*(?:优惠|折扣|半价)"),
            re.compile(r"(?:优惠|折扣).*(?:票|交通|地铁|公交|lrt|mrt)"),
            re.compile(r"(?:怎么|如何).*(?:打折|优惠)"),
        ),
    ),
    (
        "ticket_guide",
        (
            re.compile(r"\b(?:buy|purchase|get)\s+(?:a\s+)?tickets?\b", re.I),
            re.compile(r"\bhow\s+(?:do\s+i|to)\s+.{0,40}\b(?:buy|purchase)\b.*\btickets?\b", re.I),
            re.compile(r"\b(?:touch\s*'?n\s*go|tng|token)\b", re.I),
            re.compile(r"\bticket\s+(?:guide|machine|counter)\b", re.I),
            re.compile(r"\b(?:beli|membeli)\s+tiket\b", re.I),
            re.compile(r"(?:怎么|如何).*(?:买票|购票)"),
            re.compile(r"\b(?:fare|fares|tambang)\b(?!.*\bconcession\b)", re.I),
        ),
    ),
    (
        "privacy",
        (
            re.compile(r"\bprivacy\b", re.I),
            re.compile(r"\b(?:data protection|pdpa|personal data)\b", re.I),
            re.compile(r"\bprivasi\b", re.I),
            re.compile(r"(?:隐私|个人数据)"),
        ),
    ),
    (
        "preference",
        (
            re.compile(r"\b(?:preference|preferences|travel preference)\b", re.I),
            re.compile(r"\b(?:accessibility first|least walk|fewest transfer)\b", re.I),
            re.compile(r"\bkeutamaan\b", re.I),
            re.compile(r"(?:偏好|无障碍优先|少走路)"),
        ),
    ),
)

_CLARIFY_YES = re.compile(
    r"^(?:yes|yeah|yep|yup|correct|right|that's right|that is right|ok|okay|sure|"
    r"ya|betul|benar|"
    r"是|对|没错|嗯|好)[.!?]*$",
    re.I,
)


def infer_probable_guide_intent(message: str) -> GuideIntent | None:
    text = (message or "").strip()
    if not text:
        return None
    for intent, patterns in _TOPIC_RULES:
        if any(pattern.search(text) for pattern in patterns):
            return intent
    return None


def is_clarify_confirmation(message: str) -> bool:
    return bool(_CLARIFY_YES.match(message.strip()))


def guide_action_for_intent(intent: GuideIntent) -> ChatAction:
    action_map = {
        "ticket_guide": ChatAction(type="open_ticket_guide"),
        "concession_guide": ChatAction(type="open_concession_guide"),
        "privacy": ChatAction(type="open_privacy"),
        "preference": ChatAction(type="open_preference"),
    }
    return action_map[intent]


def blocks_inferred_topic_answer(intent: GuideIntent, language: str) -> list[ChatBlock]:
    """Friendly clarification + short answer when the user uses informal wording."""
    topics: dict[GuideIntent, dict[str, dict[str, str]]] = {
        "concession_guide": {
            "heading": {
                "en": "Senior travel discount",
                "ms": "Diskaun perjalanan warga emas",
                "zh": "长者出行优惠",
            },
            "lead": {
                "en": (
                    "It sounds like you are asking about senior concession fares "
                    "(discounted public transport for older adults in Malaysia)."
                ),
                "ms": (
                    "Nampaknya anda bertanya tentang tambang konsesi warga emas "
                    "(tambang pengangkutan awam berdiskaun untuk warga emas di Malaysia)."
                ),
                "zh": "听起来您想了解长者/乐龄公共交通优惠票价（马来西亚的老年人乘车折扣）。",
            },
            "bullets": {
                "en": [
                    "ElderGo KL shows a simple guide — it cannot apply for you in the app.",
                    "You usually need a valid MyKad and apply at a concession registration counter.",
                    "After approval, you can use your card on LRT, MRT, buses, and BRT.",
                ],
                "ms": [
                    "ElderGo KL menunjukkan panduan ringkas — ia tidak boleh memohon untuk anda dalam app.",
                    "Anda biasanya perlukan MyKad sah dan daftar di kaunter konsesi.",
                    "Selepas lulus, anda boleh guna kad pada LRT, MRT, bas, dan BRT.",
                ],
                "zh": [
                    "ElderGo KL 提供简明指南——不能在 App 内代您申请。",
                    "通常需要有效 MyKad，并到优惠登记柜台办理。",
                    "获批后可在 LRT、MRT、巴士和 BRT 使用。",
                ],
            },
            "cta": {
                "en": "Tap below to open the senior concession guide with step-by-step pictures.",
                "ms": "Tekan di bawah untuk buka panduan konsesi warga emas dengan langkah bergambar.",
                "zh": "点击下方打开长者优惠指南，查看分步说明。",
            },
        },
        "ticket_guide": {
            "heading": {
                "en": "Buying tickets",
                "ms": "Membeli tiket",
                "zh": "如何买票",
            },
            "lead": {
                "en": "It sounds like you want to know how to buy or use tickets for public transport.",
                "ms": "Nampaknya anda mahu tahu cara membeli atau menggunakan tiket pengangkutan awam.",
                "zh": "听起来您想了解如何购买或使用公共交通车票。",
            },
            "bullets": {
                "en": [
                    "ElderGo KL shows ticket steps only — it cannot sell tickets in the app.",
                    "At the station: use a ticket machine, counter, or Touch 'n Go card.",
                ],
                "ms": [
                    "ElderGo KL hanya menunjukkan langkah tiket — ia tidak menjual tiket dalam app.",
                    "Di stesen: guna mesin tiket, kaunter, atau kad Touch 'n Go.",
                ],
                "zh": [
                    "ElderGo KL 只提供购票步骤——不能在 App 内买票。",
                    "在车站可使用售票机、柜台或 Touch 'n Go 卡。",
                ],
            },
            "cta": {
                "en": "Tap below to open the ticket guide.",
                "ms": "Tekan di bawah untuk buka panduan tiket.",
                "zh": "点击下方打开购票指南。",
            },
        },
        "privacy": {
            "heading": {
                "en": "Privacy",
                "ms": "Privasi",
                "zh": "隐私",
            },
            "lead": {
                "en": "It sounds like you are asking how ElderGo KL handles your personal information.",
                "ms": "Nampaknya anda bertanya bagaimana ElderGo KL mengendalikan maklumat peribadi anda.",
                "zh": "听起来您想了解 ElderGo KL 如何处理您的个人信息。",
            },
            "bullets": {
                "en": [
                    "No GPS tracking, no saved travel history, and no ads.",
                    "Route details stay on your phone unless you choose to share them.",
                ],
                "ms": [
                    "Tiada penjejakan GPS, tiada sejarah perjalanan disimpan, tiada iklan.",
                    "Butiran laluan kekal di telefon melainkan anda kongsi.",
                ],
                "zh": [
                    "不追踪 GPS、不保存出行记录、无广告。",
                    "路线信息保存在您的手机上，除非您主动分享。",
                ],
            },
            "cta": {
                "en": "Tap below to read the privacy summary.",
                "ms": "Tekan di bawah untuk baca ringkasan privasi.",
                "zh": "点击下方查看隐私说明。",
            },
        },
        "preference": {
            "heading": {
                "en": "Travel preferences",
                "ms": "Keutamaan perjalanan",
                "zh": "出行偏好",
            },
            "lead": {
                "en": "It sounds like you want to adjust how routes are chosen for you.",
                "ms": "Nampaknya anda mahu laraskan cara laluan dipilih untuk anda.",
                "zh": "听起来您想调整路线推荐方式。",
            },
            "bullets": {
                "en": [
                    "You can turn on Accessibility first, Least walk, or Fewest transfers.",
                    "Save what feels comfortable before you search for a route.",
                ],
                "ms": [
                    "Anda boleh hidupkan Utamakan aksesibiliti, Kurang berjalan, atau Kurang pertukaran.",
                    "Simpan tetapan sebelum mencari laluan.",
                ],
                "zh": [
                    "可开启「无障碍优先」「少走路」或「少换乘」。",
                    "搜索路线前先保存您觉得舒适的设置。",
                ],
            },
            "cta": {
                "en": "Tap below to open Preferences.",
                "ms": "Tekan di bawah untuk buka Keutamaan.",
                "zh": "点击下方打开偏好设置。",
            },
        },
    }

    copy = topics[intent]
    return [
        ChatBlock(type="heading", text=copy["heading"][language]),
        ChatBlock(type="paragraph", text=copy["lead"][language]),
        ChatBlock(type="bullets", items=copy["bullets"][language]),
        ChatBlock(type="callout", tone="info", text=copy["cta"][language]),
    ]
