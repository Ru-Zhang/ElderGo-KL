"""Structured chat answer blocks for elderly-friendly rendering."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError

from app.schemas.ai import ChatBlock, KeyValueRow, SourceLink

ALLOWED_SOURCE_URLS: dict[str, str] = {
    "myrapid": "https://myrapid.com.my/",
    "mrt": "https://www.mrt.com.my/",
    "openweather": "https://openweathermap.org/",
}

OFFICIAL_SOURCES: dict[str, dict[str, list[SourceLink]]] = {
    "ticket": {
        "en": [SourceLink(title="MyRapid — fares and tickets", url=ALLOWED_SOURCE_URLS["myrapid"], org="MyRapid")],
        "ms": [SourceLink(title="MyRapid — tambang dan tiket", url=ALLOWED_SOURCE_URLS["myrapid"], org="MyRapid")],
        "zh": [SourceLink(title="MyRapid — 票价与票务", url=ALLOWED_SOURCE_URLS["myrapid"], org="MyRapid")],
    },
    "concession": {
        "en": [SourceLink(title="MyRapid — travel information", url=ALLOWED_SOURCE_URLS["myrapid"], org="MyRapid")],
        "ms": [SourceLink(title="MyRapid — maklumat perjalanan", url=ALLOWED_SOURCE_URLS["myrapid"], org="MyRapid")],
        "zh": [SourceLink(title="MyRapid — 出行信息", url=ALLOWED_SOURCE_URLS["myrapid"], org="MyRapid")],
    },
    "weather": {
        "en": [SourceLink(title="OpenWeather", url=ALLOWED_SOURCE_URLS["openweather"], org="OpenWeather")],
        "ms": [SourceLink(title="OpenWeather", url=ALLOWED_SOURCE_URLS["openweather"], org="OpenWeather")],
        "zh": [SourceLink(title="OpenWeather", url=ALLOWED_SOURCE_URLS["openweather"], org="OpenWeather")],
    },
}


def _hours_plain_lines(raw: str, language: str) -> list[str]:
    from app.utils.hours_parser import parse_hours_summary

    parsed = parse_hours_summary(raw)
    if not parsed:
        return [line.strip() for line in raw.split("\n") if line.strip()]

    open_l = {"en": "Open", "ms": "Buka", "zh": "开"}[language]
    close_l = {"en": "Close", "ms": "Tutup", "zh": "关"}[language]
    last_l = {"en": "Last train to", "ms": "Tren terakhir ke", "zh": "末班车往"}[language]
    lines: list[str] = []
    for entry in parsed.open:
        cond = f" ({entry.condition})" if entry.condition else ""
        lines.append(f"- {open_l}: {entry.time}{cond}")
    for entry in parsed.close:
        cond = f" ({entry.condition})" if entry.condition else ""
        lines.append(f"- {close_l}: {entry.time}{cond}")
    for dest in parsed.last_trains:
        for entry in dest.values:
            cond = f" ({entry.condition})" if entry.condition else ""
            lines.append(f"- {last_l} {dest.to}: {entry.time}{cond}")
    lines.extend(f"- {other}" for other in parsed.other)
    return lines


def blocks_to_plain_text(blocks: list[ChatBlock]) -> str:
    """Accessible plain-text fallback from structured blocks."""
    lines: list[str] = []
    for block in blocks:
        if block.type == "heading" and block.text:
            lines.append(block.text)
        elif block.type == "paragraph" and block.text:
            lines.append(block.text)
        elif block.type in ("bullets", "numbered") and block.items:
            for index, item in enumerate(block.items, start=1):
                prefix = f"{index}. " if block.type == "numbered" else "- "
                lines.append(f"{prefix}{item}")
        elif block.type == "key_values" and block.rows:
            for row in block.rows:
                lines.append(f"- {row.label}: {row.value}")
        elif block.type == "callout" and block.text:
            lines.append(block.text)
        elif block.type == "hours" and block.text:
            lines.extend(_hours_plain_lines(block.text, "en"))
        elif block.type == "sources" and block.links:
            for link in block.links:
                lines.append(f"- {link.title}: {link.url}")
        elif block.type == "place_cards" and block.links:
            for link in block.links:
                lines.append(f"- {link.title}: {link.url}")
    return "\n".join(lines).strip()


def dedupe_sources_blocks(blocks: list[ChatBlock]) -> list[ChatBlock]:
    """Collapse repeated sources blocks (e.g. overview + local weather both cite OpenWeather)."""
    non_source: list[ChatBlock] = []
    merged_links: list[SourceLink] = []
    seen_urls: set[str] = set()
    sources_heading: str | None = None

    for block in blocks:
        if block.type != "sources" or not block.links:
            non_source.append(block)
            continue
        if block.text and not sources_heading:
            sources_heading = block.text
        for link in block.links:
            key = link.url.rstrip("/")
            if key in seen_urls:
                continue
            seen_urls.add(key)
            merged_links.append(link)

    if not merged_links:
        return blocks
    return [
        *non_source,
        ChatBlock(
            type="sources",
            text=sources_heading or "Official information",
            links=merged_links,
        ),
    ]


def append_official_sources(
    blocks: list[ChatBlock],
    context: str,
    language: str,
    *,
    extra_links: list[SourceLink] | None = None,
) -> list[ChatBlock]:
    catalog = OFFICIAL_SOURCES.get(context, {}).get(language, [])
    links = list(catalog)
    if extra_links:
        for link in extra_links:
            if _is_allowed_url(link.url):
                links.append(link)
    if not links:
        return blocks
    deduped: list[SourceLink] = []
    seen: set[str] = set()
    for link in links:
        key = link.url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(link)
    if not deduped:
        return blocks
    return [
        *blocks,
        ChatBlock(
            type="sources",
            text=_sources_heading(language),
            links=deduped,
        ),
    ]


def _sources_heading(language: str) -> str:
    return {
        "en": "Official information",
        "ms": "Maklumat rasmi",
        "zh": "官方信息",
    }.get(language, "Official information")


def _is_allowed_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        host = (parsed.netloc or "").lower()
        for allowed in ALLOWED_SOURCE_URLS.values():
            allowed_host = urlparse(allowed).netloc.lower()
            if host == allowed_host or host.endswith(f".{allowed_host}"):
                return True
        return url.strip().rstrip("/") in {u.rstrip("/") for u in ALLOWED_SOURCE_URLS.values()}
    except Exception:
        return False


def sanitize_source_links(links: list[SourceLink] | None) -> list[SourceLink]:
    if not links:
        return []
    cleaned: list[SourceLink] = []
    for link in links:
        if _is_allowed_url(link.url):
            cleaned.append(link)
    return cleaned


def blocks_from_plain_text(text: str) -> list[ChatBlock]:
    """Wrap legacy plain answers as paragraph + bullet blocks."""
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []
    blocks: list[ChatBlock] = []
    buffer: list[str] = []
    list_items: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if buffer:
            blocks.append(ChatBlock(type="paragraph", text=" ".join(buffer)))
            buffer.clear()

    def flush_list() -> None:
        nonlocal list_kind, list_items
        if list_items and list_kind:
            blocks.append(ChatBlock(type=list_kind, items=list(list_items)))  # type: ignore[arg-type]
        list_items = []
        list_kind = None

    for line in normalized.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        ordered = re.match(r"^\d+\.\s+(.*)$", stripped)
        bullet = re.match(r"^[-*+]\s+(.*)$", stripped)
        if ordered:
            flush_paragraph()
            if list_kind != "numbered":
                flush_list()
                list_kind = "numbered"
            list_items.append(ordered.group(1).strip())
            continue
        if bullet:
            flush_paragraph()
            if list_kind != "bullets":
                flush_list()
                list_kind = "bullets"
            list_items.append(bullet.group(1).strip())
            continue
        flush_list()
        buffer.append(stripped)
    flush_paragraph()
    flush_list()
    return blocks


def blocks_for_station(detail, language: str) -> list[ChatBlock]:
    status_labels = {
        "supported": {"en": "Supported", "ms": "Disokong", "zh": "支持"},
        "not_supported": {"en": "Not supported", "ms": "Tidak disokong", "zh": "不支持"},
        "unknown": {"en": "Unknown", "ms": "Tidak diketahui", "zh": "未知"},
    }
    emphasis_map = {
        "supported": "supported",
        "not_supported": "not_supported",
        "unknown": "unknown",
    }
    status_key = detail.accessibility_status if detail.accessibility_status in status_labels else "unknown"
    status = status_labels[status_key][language]
    routes = ", ".join(detail.routes) if detail.routes else "-"
    facilities = ", ".join(detail.known_facilities or detail.station_facilities or []) or "-"
    hours_raw = (detail.station_hours_summary or "").strip()
    address = detail.station_address or "-"

    heading = {
        "en": f"Station: {detail.name}",
        "ms": f"Stesen: {detail.name}",
        "zh": f"站点：{detail.name}",
    }[language]
    intro = {
        "en": "Summary from ElderGo KL station data:",
        "ms": "Ringkasan daripada data stesen ElderGo KL:",
        "zh": "来自 ElderGo KL 站点数据的摘要：",
    }[language]
    cta = {
        "en": "Tap the button below to open the full station page with photos and more details.",
        "ms": "Tekan butang di bawah untuk buka halaman stesen penuh dengan gambar dan butiran lanjut.",
        "zh": "点击下方按钮打开完整站点页面（含图片与更多详情）。",
    }[language]

    blocks: list[ChatBlock] = [
        ChatBlock(type="heading", text=heading),
        ChatBlock(type="paragraph", text=intro),
        ChatBlock(
            type="key_values",
            rows=[
                KeyValueRow(
                    label={"en": "Accessibility", "ms": "Kebolehcapaian", "zh": "无障碍"}[language],
                    value=status,
                    emphasis=emphasis_map.get(status_key, "neutral"),  # type: ignore[arg-type]
                ),
                KeyValueRow(
                    label={"en": "Lines", "ms": "Laluan", "zh": "线路"}[language],
                    value=routes,
                ),
                KeyValueRow(
                    label={"en": "Facilities", "ms": "Kemudahan", "zh": "设施"}[language],
                    value=facilities,
                ),
                KeyValueRow(
                    label={"en": "Address", "ms": "Alamat", "zh": "地址"}[language],
                    value=address,
                ),
            ],
        ),
    ]

    if hours_raw:
        from app.utils.hours_parser import parse_hours_summary

        if parse_hours_summary(hours_raw):
            blocks.append(ChatBlock(type="hours", text=hours_raw))
        else:
            blocks[-1].rows.append(  # type: ignore[union-attr]
                KeyValueRow(
                    label={"en": "Hours", "ms": "Waktu operasi", "zh": "营业时间"}[language],
                    value=hours_raw,
                )
            )

    blocks.extend(
        [
            ChatBlock(type="callout", tone="info", text=cta),
        ]
    )

    extra: list[SourceLink] = []
    facility_url = getattr(detail, "facility_source_url", None)
    if facility_url and _is_allowed_url(facility_url):
        extra.append(
            SourceLink(
                title={"en": "MRT station page", "ms": "Halaman stesen MRT", "zh": "MRT 站点页面"}[language],
                url=facility_url,
                org="MRT Corp",
            )
        )
    return append_official_sources(blocks, "station", language, extra_links=extra)


def blocks_for_weather(forecast, language: str, *, region_label: str | None = None) -> list[ChatBlock]:
    label = region_label or forecast.destination_name
    risk = forecast.risk_level or "clear"
    risk_hints = {
        "clear": {
            "en": "Good for travel",
            "ms": "Sesuai untuk perjalanan",
            "zh": "较适合出行",
        },
        "rain": {
            "en": "Rain likely — allow extra time",
            "ms": "Hujan mungkin — beri masa tambahan",
            "zh": "可能下雨——请预留时间",
        },
        "hot": {
            "en": "Hot — travel slowly and drink water",
            "ms": "Panas — bergerak perlahan dan minum air",
            "zh": "较热——请慢行并补水",
        },
        "storm": {
            "en": "Storm possible — consider delaying trips",
            "ms": "Ribut mungkin — pertimbangkan tangguh perjalanan",
            "zh": "可能有暴风雨——可延后出行",
        },
        "unavailable": {
            "en": "Weather temporarily unavailable",
            "ms": "Cuaca tidak tersedia buat sementara waktu",
            "zh": "天气暂不可用",
        },
    }
    callout_tone = "warning" if risk in ("rain", "storm", "hot") else "success" if risk == "clear" else "info"
    summary = risk_hints.get(risk, risk_hints["clear"])[language]
    condition = (forecast.weather_description or "").strip().capitalize() or "—"
    temp_line = f"{forecast.temperature_c}°C · {condition}"

    heading = {
        "en": f"Weather — {label}",
        "ms": f"Cuaca — {label}",
        "zh": f"{label} 天气",
    }[language]

    feels_label = {"en": "Feels like", "ms": "Rasa seperti", "zh": "体感"}[language]
    blocks: list[ChatBlock] = [
        ChatBlock(type="heading", text=heading),
        ChatBlock(
            type="callout",
            tone=callout_tone,
            text=f"{temp_line}\n{feels_label}: {forecast.feels_like_c}°C\n{summary}",
        ),
    ]

    advice = [line.strip() for line in (forecast.senior_advice or [])[:3] if line and line.strip()]
    if advice:
        blocks.append(
            ChatBlock(
                type="bullets",
                items=advice,
            )
        )

    travel_tips = {
        "rain": {
            "en": "Use covered walkways and hold handrails when it is wet.",
            "ms": "Guna laluan bertutup dan pegang pemegang apabila lantai basah.",
            "zh": "雨天请走有顶棚的路，扶好扶手。",
        },
        "hot": {
            "en": "Rest in shade or air-conditioning if you feel tired.",
            "ms": "Berehat di tempat teduh atau berhawa dingin jika letih.",
            "zh": "若疲劳，可在阴凉处或空调区休息。",
        },
        "storm": {
            "en": "Ask station staff for help; prefer lifts over long outdoor walks.",
            "ms": "Minta bantuan staf stesen; utamakan lif.",
            "zh": "可向车站工作人员求助，优先乘电梯。",
        },
    }
    if risk in travel_tips:
        blocks.append(ChatBlock(type="callout", tone="warning", text=travel_tips[risk][language]))

    return append_official_sources(blocks, "weather", language)


def blocks_for_kv_weather_overview(forecast, language: str) -> list[ChatBlock]:
    intro = {
        "en": "Klang Valley overview (Kuala Lumpur area)",
        "ms": "Gambaran Lembah Klang (kawasan Kuala Lumpur)",
        "zh": "巴生谷概览（吉隆坡一带）",
    }[language]
    detail_blocks = blocks_for_weather(forecast, language, region_label="Kuala Lumpur")
    if detail_blocks and detail_blocks[0].type == "heading":
        detail_blocks[0] = ChatBlock(type="heading", text=intro)
    return detail_blocks


def blocks_simple_prompt(heading: str, body: str, *, examples: list[str] | None = None) -> list[ChatBlock]:
    blocks: list[ChatBlock] = [
        ChatBlock(type="heading", text=heading),
        ChatBlock(type="paragraph", text=body),
    ]
    if examples:
        blocks.append(ChatBlock(type="bullets", items=examples))
    return blocks


def _blocks_simple_prompt_localized(
    heading: str, body: str, language: str, *, examples: list[str] | None = None
) -> list[ChatBlock]:
    blocks: list[ChatBlock] = [
        ChatBlock(type="heading", text=heading),
        ChatBlock(type="paragraph", text=body),
    ]
    if examples:
        blocks.append(
            ChatBlock(
                type="callout",
                tone="info",
                text={
                    "en": "Type your answer in the box below, then press Send.",
                    "ms": "Taip jawapan dalam kotak di bawah, kemudian tekan Hantar.",
                    "zh": "请在下方输入框输入后发送。",
                }[language],
            )
        )
        blocks.append(ChatBlock(type="bullets", items=examples))
    return blocks


def blocks_ask_station(language: str) -> list[ChatBlock]:
    return _blocks_simple_prompt_localized(
        {"en": "Station information", "ms": "Maklumat stesen", "zh": "站点信息"}[language],
        {
            "en": "Which station would you like to know about?",
            "ms": "Stesen manakah yang anda mahu tahu?",
            "zh": "您想查询哪个站点？",
        }[language],
        language,
        examples=[
            {"en": "Type a station name, e.g. KL Sentral, Subang Jaya, USJ 7", "ms": "Taip nama stesen, cth. KL Sentral, Subang Jaya, USJ 7", "zh": "请输入站点名称，例如 KL Sentral、Subang Jaya"}[language]
        ],
    )


def blocks_ask_weather_location(language: str) -> list[ChatBlock]:
    return _blocks_simple_prompt_localized(
        {"en": "Weather check", "ms": "Semak cuaca", "zh": "天气查询"}[language],
        {
            "en": "Which area in the Klang Valley would you like weather for?",
            "ms": "Kawasan manakah dalam Lembah Klang yang anda mahu cuaca?",
            "zh": "您想查询巴生谷哪个区域的天气？",
        }[language],
        language,
        examples=[
            {"en": "Subang Jaya, KLCC, Petaling Jaya", "ms": "Subang Jaya, KLCC, Petaling Jaya", "zh": "Subang Jaya、KLCC、Petaling Jaya"}[language]
        ],
    )


def blocks_ask_route_origin(language: str) -> list[ChatBlock]:
    return _blocks_simple_prompt_localized(
        {"en": "Plan your route", "ms": "Rancang laluan", "zh": "规划路线"}[language],
        {
            "en": "Where will you start from? (From)",
            "ms": "Dari mana anda akan bermula? (Dari)",
            "zh": "您从哪里出发？（起点 From）",
        }[language],
        language,
        examples=[
            {"en": "Type a place in the Klang Valley, e.g. Monash University, KL Sentral", "ms": "Taip tempat dalam Lembah Klang, cth. Monash University, KL Sentral", "zh": "请输入巴生谷内的地点"}[language]
        ],
    )


def blocks_ask_route_destination(language: str) -> list[ChatBlock]:
    return _blocks_simple_prompt_localized(
        {"en": "Plan your route", "ms": "Rancang laluan", "zh": "规划路线"}[language],
        {
            "en": "Where would you like to go? (To)",
            "ms": "Ke mana anda mahu pergi? (Ke)",
            "zh": "您要去哪里？（终点 To）",
        }[language],
        language,
        examples=[
            {"en": "Type your destination, e.g. KLCC, Sunway Pyramid", "ms": "Taip destinasi, cth. KLCC, Sunway Pyramid", "zh": "请输入目的地，例如 KLCC"}[language]
        ],
    )


def blocks_ask_departure_time(language: str) -> list[ChatBlock]:
    return _blocks_simple_prompt_localized(
        {"en": "When are you travelling?", "ms": "Bila anda bergerak?", "zh": "什么时候出发？"}[language],
        {
            "en": "Reply with one option:",
            "ms": "Balas dengan satu pilihan:",
            "zh": "请回复其中一个选项：",
        }[language],
        language,
        examples=[
            {
                "en": "now, morning rush, midday, evening rush, night — or e.g. tomorrow 6am (or 1–5)",
                "ms": "sekarang, puncak pagi, tengah hari, puncak petang, malam — atau cth. esok 6 pagi (atau 1–5)",
                "zh": "现在、早高峰、午间、晚高峰、夜间 — 或例如 明天 6点（或 1–5）",
            }[language]
        ],
    )


def blocks_pick_list(
    intro: str,
    candidates: list[dict],
    language: str,
) -> list[ChatBlock]:
    items = []
    for index, item in enumerate(candidates[:3], start=1):
        label = item.get("label") or item.get("name") or ""
        items.append(f"{label}")
    return [
        ChatBlock(type="paragraph", text=intro),
        ChatBlock(type="numbered", items=items),
        ChatBlock(
            type="callout",
            tone="info",
            text={
                "en": "Reply with the number (1, 2, 3) or copy the exact name from the list.",
                "ms": "Balas dengan nombor (1, 2, 3) atau salin nama tepat dari senarai.",
                "zh": "请回复编号（1、2、3）或复制列表中的准确名称。",
            }[language],
        ),
    ]


def blocks_station_pick(candidates: list[dict], language: str) -> list[ChatBlock]:
    intro = {
        "en": "I found a few stations. Please choose one:",
        "ms": "Saya jumpa beberapa stesen. Sila pilih satu:",
        "zh": "找到多个站点，请选择一个：",
    }[language]
    return blocks_pick_list(intro, candidates, language)


def blocks_place_pick(candidates: list[dict], language: str) -> list[ChatBlock]:
    intro = {
        "en": "I found a few places. Please choose one:",
        "ms": "Saya jumpa beberapa tempat. Sila pilih satu:",
        "zh": "找到多个地点，请选择一个：",
    }[language]
    return blocks_pick_list(intro, candidates, language)


def blocks_exploratory_places(
    places: list[dict],
    language: str,
    *,
    search_label: str | None = None,
) -> list[ChatBlock]:
    """Places from Google Text Search (deterministic POI exploration)."""
    heading = {
        "en": "Places in the Klang Valley",
        "ms": "Tempat dalam Lembah Klang",
        "zh": "巴生谷地点",
    }[language]
    blocks: list[ChatBlock] = [ChatBlock(type="heading", text=heading)]
    if search_label:
        blocks.append(
            ChatBlock(
                type="paragraph",
                text={
                    "en": f"Results for: {search_label}",
                    "ms": f"Hasil untuk: {search_label}",
                    "zh": f"搜索结果：{search_label}",
                }[language],
            )
        )
    items = []
    for place in places[:3]:
        name = (place.get("label") or place.get("name") or "").strip()
        address = (place.get("address") or "").strip()
        if address and address.lower() not in name.lower():
            items.append(f"{name} — {address}")
        else:
            items.append(name)
    if items:
        blocks.append(ChatBlock(type="numbered", items=items))
    blocks.append(
        ChatBlock(
            type="callout",
            tone="info",
            text={
                "en": "For step-by-step transit directions, use Plan a route below.",
                "ms": "Untuk arah transit langkah demi langkah, gunakan Rancang laluan di bawah.",
                "zh": "如需逐步公交路线，请使用下方的规划路线。",
            }[language],
        )
    )
    blocks.append(
        ChatBlock(
            type="sources",
            text={
                "en": "Place data",
                "ms": "Data tempat",
                "zh": "地点数据",
            }[language],
            links=[
                SourceLink(
                    title="Google Maps",
                    url="https://www.google.com/maps",
                    org="Google",
                )
            ],
        )
    )
    return blocks


def blocks_maps_grounding_places(
    places: list[dict],
    language: str,
    *,
    summary: str | None = None,
) -> list[ChatBlock]:
    """Up to 3 POIs from Gemini Maps grounding metadata."""
    heading = {
        "en": "Nearby places (Klang Valley)",
        "ms": "Tempat berhampiran (Lembah Klang)",
        "zh": "附近地点（巴生谷）",
    }[language]
    blocks: list[ChatBlock] = [ChatBlock(type="heading", text=heading)]
    if summary:
        blocks.append(ChatBlock(type="paragraph", text=summary.strip()))
    links: list[SourceLink] = []
    for place in places[:3]:
        title = (place.get("title") or "").strip()
        url = (place.get("url") or "").strip()
        if title and url:
            links.append(SourceLink(title=title, url=url, org="Google Maps"))
    if links:
        blocks.append(ChatBlock(type="place_cards", links=links))
    blocks.append(
        ChatBlock(
            type="callout",
            tone="info",
            text={
                "en": "For ElderGo step-by-step routes, tap Plan a route.",
                "ms": "Untuk laluan langkah demi langkah ElderGo, tekan Rancang laluan.",
                "zh": "如需 ElderGo 逐步路线，请点规划路线。",
            }[language],
        )
    )
    blocks.append(
        ChatBlock(
            type="sources",
            text={
                "en": "Place data",
                "ms": "Data tempat",
                "zh": "地点数据",
            }[language],
            links=[
                SourceLink(
                    title="Google Maps",
                    url="https://www.google.com/maps",
                    org="Google",
                )
            ],
        )
    )
    return blocks


def blocks_pick_retry(intro: str, candidates: list[dict], language: str) -> list[ChatBlock]:
    return blocks_pick_list(intro, candidates, language)


def blocks_error_short_input(language: str) -> list[ChatBlock]:
    """Backward-compatible alias for too-short place input."""
    return blocks_place_input_error("too_short", language)


_PLACE_INPUT_MESSAGES: dict[str, dict[str, str]] = {
    "too_short": {
        "en": "That looks too short to be a place name. Please type a full location in the Klang Valley (for example: KL Sentral, Subang Jaya, KLCC).",
        "ms": "Input itu terlalu pendek untuk nama tempat. Sila taip lokasi penuh dalam Lembah Klang (contoh: KL Sentral, Subang Jaya, KLCC).",
        "zh": "输入太短，不像地点名称。请输入巴生谷完整地点（例如：KL Sentral、Subang Jaya、KLCC）。",
    },
    "empty": {
        "en": "Please type a place name in the Klang Valley (for example: Monash University, KL Sentral, KLCC).",
        "ms": "Sila taip nama tempat dalam Lembah Klang (contoh: Monash University, KL Sentral, KLCC).",
        "zh": "请输入巴生谷内的地点名称（例如：Monash University、KL Sentral、KLCC）。",
    },
    "too_long": {
        "en": "That looks like a long message. Please type one place name only, or send your full trip in one sentence (for example: from Monash University to KLCC).",
        "ms": "Mesej itu terlalu panjang. Sila taip satu nama tempat sahaja, atau hantar perjalanan penuh dalam satu ayat (contoh: dari Monash University ke KLCC).",
        "zh": "这条消息太长了。请只输入一个地点名称，或在一句话里说明完整行程（例如：从 Monash University 到 KLCC）。",
    },
    "route_sentence": {
        "en": "I can plan that in one step. Please send both places together (for example: from Monash University to KLIA), or type only the place this step is asking for.",
        "ms": "Saya boleh rancang dalam satu langkah. Sila hantar kedua-dua tempat sekali (contoh: dari Monash University ke KLIA), atau taip hanya tempat yang diminta pada langkah ini.",
        "zh": "我可以一步帮您规划。请在一句话里同时说明起点和终点（例如：从 Monash University 到 KLIA），或只输入当前步骤询问的那一个地点。",
    },
    "implausible": {
        "en": "I could not read that as a place name. Please use letters and familiar area names in the Klang Valley (for example: Petaling Jaya, Sunway, KL Sentral).",
        "ms": "Saya tidak dapat baca itu sebagai nama tempat. Sila gunakan huruf dan nama kawasan biasa dalam Lembah Klang (contoh: Petaling Jaya, Sunway, KL Sentral).",
        "zh": "无法把输入识别为地点名称。请使用巴生谷常见地名（例如：Petaling Jaya、Sunway、KL Sentral）。",
    },
}


def blocks_place_input_error(issue: str, language: str) -> list[ChatBlock]:
    text = _PLACE_INPUT_MESSAGES.get(issue, _PLACE_INPUT_MESSAGES["implausible"])[language]
    return [ChatBlock(type="callout", tone="warning", text=text)]


def blocks_station_not_found(language: str) -> list[ChatBlock]:
    return [
        ChatBlock(
            type="callout",
            tone="warning",
            text={
                "en": "I could not find that station. Please check the spelling or try another station name.",
                "ms": "Saya tidak jumpa stesen itu. Sila semak ejaan atau cuba nama stesen lain.",
                "zh": "找不到该站点。请检查拼写或尝试其他站点名称。",
            }[language],
        )
    ]


def blocks_place_not_found(language: str) -> list[ChatBlock]:
    return [
        ChatBlock(
            type="callout",
            tone="warning",
            text={
                "en": "I couldn't find that place in the Klang Valley. Please check the spelling or try a nearby landmark (for example: KL Sentral, Petaling Jaya).",
                "ms": "Saya tidak jumpa tempat itu dalam Lembah Klang. Sila semak ejaan atau cuba mercu tanda berhampiran (contoh: KL Sentral, Petaling Jaya).",
                "zh": "在巴生谷找不到该地点。请检查拼写或尝试附近地标（例如：KL Sentral、Petaling Jaya）。",
            }[language],
        )
    ]


def blocks_weather_not_found(language: str) -> list[ChatBlock]:
    return [
        ChatBlock(
            type="callout",
            tone="warning",
            text={
                "en": "I could not find that place in the Klang Valley. Please type a full area name (for example: Subang Jaya, KLCC, Petaling Jaya).",
                "ms": "Saya tidak jumpa tempat itu dalam Lembah Klang. Sila taip nama kawasan penuh (contoh: Subang Jaya, KLCC, Petaling Jaya).",
                "zh": "在巴生谷找不到该地点。请输入完整区域名称（例如：Subang Jaya、KLCC、Petaling Jaya）。",
            }[language],
        )
    ]


def blocks_invalid_departure(language: str) -> list[ChatBlock]:
    return [
        ChatBlock(
            type="callout",
            tone="warning",
            text={
                "en": "Please choose: now, morning rush, midday, evening rush, or night (or reply 1–5).",
                "ms": "Sila pilih: sekarang, puncak pagi, tengah hari, puncak petang, atau malam (atau balas 1–5).",
                "zh": "请选择：现在、早高峰、午间、晚高峰或夜间（也可回复 1–5）。",
            }[language],
        )
    ]


def blocks_route_ready(
    origin_label: str,
    destination_label: str,
    departure: str,
    language: str,
) -> list[ChatBlock]:
    blocks: list[ChatBlock] = [
        ChatBlock(
            type="heading",
            text={"en": "Your route is ready", "ms": "Laluan anda sudah siap", "zh": "您的路线已准备好"}[language],
        ),
        ChatBlock(
            type="key_values",
            rows=[
                KeyValueRow(
                    label={"en": "From", "ms": "Dari", "zh": "起点 From"}[language],
                    value=origin_label,
                    emphasis="route_endpoint",
                ),
                KeyValueRow(
                    label={"en": "To", "ms": "Ke", "zh": "终点 To"}[language],
                    value=destination_label,
                    emphasis="route_endpoint",
                ),
                KeyValueRow(
                    label={"en": "Travel time", "ms": "Masa", "zh": "出行时间"}[language],
                    value=departure,
                ),
            ],
        ),
        ChatBlock(
            type="callout",
            tone="success",
            text={
                "en": "Tap the button below to open your step-by-step route.",
                "ms": "Tekan butang di bawah untuk buka langkah laluan anda.",
                "zh": "点击下方按钮打开逐步路线指引。",
            }[language],
        ),
    ]
    return blocks


def blocks_for_guide(intent: str, language: str) -> list[ChatBlock]:
    guides: dict[str, dict[str, list[ChatBlock]]] = {
        "ticket_guide": {
            "en": [
                ChatBlock(type="heading", text="Buying train tickets"),
                ChatBlock(
                    type="paragraph",
                    text="ElderGo KL shows steps only — it cannot sell tickets or take payment in the app.",
                ),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Open the ticket guide in Help for simple pictures and steps.",
                        "At the station: use the ticket machine, counter, or tap a Touch 'n Go card.",
                        "Touch 'n Go means tap your card at the gate — no paper ticket needed.",
                    ],
                ),
                ChatBlock(
                    type="callout",
                    tone="info",
                    text="You can open the ticket guide now and read it before you travel.",
                ),
            ],
            "ms": [
                ChatBlock(type="heading", text="Membeli tiket kereta api"),
                ChatBlock(
                    type="paragraph",
                    text="ElderGo KL hanya menunjukkan langkah — ia tidak menjual tiket atau mengambil bayaran dalam app.",
                ),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Buka panduan tiket di Help untuk gambar dan langkah mudah.",
                        "Di stesen: guna mesin tiket, kaunter, atau kad Touch 'n Go.",
                        "Touch 'n Go: sentuh kad di pintu masuk — tiada tiket kertas diperlukan.",
                    ],
                ),
                ChatBlock(
                    type="callout",
                    tone="info",
                    text="Anda boleh buka panduan tiket sekarang sebelum bergerak.",
                ),
            ],
            "zh": [
                ChatBlock(type="heading", text="购买火车票"),
                ChatBlock(type="paragraph", text="ElderGo KL 只提供指南，不能在 App 内买票或付款。"),
                ChatBlock(
                    type="bullets",
                    items=[
                        "在 Help 中打开买票指南查看图文步骤。",
                        "在车站：使用售票机、柜台，或 Touch 'n Go 卡。",
                        "Touch 'n Go：在闸机拍卡即可，无需纸质票。",
                    ],
                ),
                ChatBlock(type="callout", tone="info", text="您可以现在打开指南，出发前先看一遍。"),
            ],
        },
        "concession_guide": {
            "en": [
                ChatBlock(type="heading", text="Senior concession (Malaysia)"),
                ChatBlock(
                    type="paragraph",
                    text="ElderGo KL provides information only — you cannot apply inside the app.",
                ),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Malaysian citizens aged 60+ may qualify for 50% off Rapid KL rail fares.",
                        "Prepare your original MyKad (IC).",
                        "Apply at a concession registration counter (see the in-app guide).",
                    ],
                ),
                ChatBlock(type="callout", tone="info", text="Open the concession guide to see the 4 simple steps."),
            ],
            "ms": [
                ChatBlock(type="heading", text="Konsesi warga emas (Malaysia)"),
                ChatBlock(
                    type="paragraph",
                    text="ElderGo KL hanya memberi maklumat — permohonan tidak boleh dibuat dalam app.",
                ),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Warganegara Malaysia berumur 60+ mungkin layak diskaun 50% tambang Rapid KL.",
                        "Sediakan MyKad asal anda.",
                        "Mohon di kaunter pendaftaran konsesi (lihat panduan dalam app).",
                    ],
                ),
                ChatBlock(type="callout", tone="info", text="Buka panduan konsesi untuk 4 langkah mudah."),
            ],
            "zh": [
                ChatBlock(type="heading", text="长者优惠（马来西亚）"),
                ChatBlock(type="paragraph", text="ElderGo KL 仅提供信息，不能在 App 内提交申请。"),
                ChatBlock(
                    type="bullets",
                    items=[
                        "60 岁以上马来西亚公民可能享受 Rapid KL 铁路票价 50% 折扣。",
                        "请携带原件 MyKad（身份证）。",
                        "在优惠登记柜台办理（见 App 内指南）。",
                    ],
                ),
                ChatBlock(type="callout", tone="info", text="打开优惠指南查看 4 个简单步骤。"),
            ],
        },
        "privacy": {
            "en": [
                ChatBlock(type="heading", text="Your privacy"),
                ChatBlock(
                    type="paragraph",
                    text="ElderGo KL is designed to help you travel with peace of mind.",
                ),
                ChatBlock(
                    type="bullets",
                    items=[
                        "No GPS tracking of your phone.",
                        "No saved travel history after you close the app.",
                        "No ads or selling your personal data.",
                    ],
                ),
                ChatBlock(type="callout", tone="success", text="Open Privacy in Help for the full promise (PDPA)."),
            ],
            "ms": [
                ChatBlock(type="heading", text="Privasi anda"),
                ChatBlock(type="paragraph", text="ElderGo KL direka untuk membantu anda bergerak dengan tenang."),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Tiada penjejakan GPS telefon anda.",
                        "Tiada sejarah perjalanan disimpan selepas tutup app.",
                        "Tiada iklan atau penjualan data peribadi.",
                    ],
                ),
                ChatBlock(type="callout", tone="success", text="Buka Privasi di Help untuk janji penuh (PDPA)."),
            ],
            "zh": [
                ChatBlock(type="heading", text="您的隐私"),
                ChatBlock(type="paragraph", text="ElderGo KL 旨在让您安心出行。"),
                ChatBlock(
                    type="bullets",
                    items=["不追踪手机 GPS。", "关闭 App 后不保存出行记录。", "无广告，不出售个人数据。"],
                ),
                ChatBlock(type="callout", tone="success", text="在 Help 中打开隐私说明查看完整承诺（PDPA）。"),
            ],
        },
        "preference": {
            "en": [
                ChatBlock(type="heading", text="Travel preferences"),
                ChatBlock(type="paragraph", text="Set options so ElderGo KL picks a route that suits you."),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Accessibility first — prefer lifts and step-free paths.",
                        "Least walk — shorter walking sections.",
                        "Fewest transfers — fewer train changes.",
                    ],
                ),
                ChatBlock(type="callout", tone="info", text="Open Preferences now and save what feels comfortable."),
            ],
            "ms": [
                ChatBlock(type="heading", text="Keutamaan perjalanan"),
                ChatBlock(type="paragraph", text="Tetapkan pilihan supaya ElderGo KL memilih laluan yang sesuai."),
                ChatBlock(
                    type="bullets",
                    items=[
                        "Utamakan aksesibiliti — utamakan lif dan laluan tanpa tangga.",
                        "Kurang berjalan — bahagian berjalan lebih pendek.",
                        "Kurang pertukaran — kurang tukar kereta api.",
                    ],
                ),
                ChatBlock(type="callout", tone="info", text="Buka Keutamaan sekarang dan simpan tetapan anda."),
            ],
            "zh": [
                ChatBlock(type="heading", text="出行偏好"),
                ChatBlock(type="paragraph", text="设置选项，让 ElderGo KL 推荐更适合您的路线。"),
                ChatBlock(
                    type="bullets",
                    items=["无障碍优先 — 偏好电梯与无台阶路径。", "少走路 — 缩短步行段。", "少换乘 — 减少转车次数。"],
                ),
                ChatBlock(type="callout", tone="info", text="现在打开偏好设置并保存。"),
            ],
        },
    }
    context_map = {
        "ticket_guide": "ticket",
        "concession_guide": "concession",
    }
    blocks = guides.get(intent, {}).get(language, [])
    if not blocks:
        return blocks_from_plain_text("")
    ctx = context_map.get(intent)
    if ctx:
        return append_official_sources(blocks, ctx, language)
    return blocks


def blocks_in_scope_help(language: str) -> list[ChatBlock]:
    return [
        ChatBlock(
            type="heading",
            text={"en": "How I can help", "ms": "Bagaimana saya boleh membantu", "zh": "我能帮您什么"}[language],
        ),
        ChatBlock(
            type="bullets",
            items={
                "en": [
                    "Plan a route in the Klang Valley.",
                    "Check weather for a place.",
                    "Look up station accessibility and facilities.",
                    "Open ticket, concession, privacy, or preference guides.",
                ],
                "ms": [
                    "Rancang laluan dalam Lembah Klang.",
                    "Semak cuaca untuk satu tempat.",
                    "Lihat kebolehcapaian dan kemudahan stesen.",
                    "Buka panduan tiket, konsesi, privasi, atau keutamaan.",
                ],
                "zh": [
                    "规划巴生谷路线。",
                    "查询某地天气。",
                    "查看站点无障碍与设施。",
                    "打开票务、优惠、隐私或偏好指南。",
                ],
            }[language],
        ),
        ChatBlock(
            type="callout",
            tone="info",
            text={
                "en": "Try a quick question below, or type what you need.",
                "ms": "Cuba soalan pantas di bawah, atau taip apa yang anda perlukan.",
                "zh": "请使用下方快捷问题，或输入您的需求。",
            }[language],
        ),
    ]


def blocks_out_of_scope(language: str) -> list[ChatBlock]:
    return [
        ChatBlock(
            type="heading",
            text={"en": "Klang Valley travel only", "ms": "Lembah Klang sahaja", "zh": "仅限巴生谷出行"}[language],
        ),
        ChatBlock(
            type="paragraph",
            text={
                "en": "I can help with routes, stations, weather, ticket guides, concessions, and how to use ElderGo KL.",
                "ms": "Saya boleh bantu laluan, stesen, cuaca, panduan tiket, konsesi, dan cara guna ElderGo KL.",
                "zh": "我可以协助路线、站点、天气、票务指南、优惠与 App 使用。",
            }[language],
        ),
        ChatBlock(
            type="callout",
            tone="info",
            text={
                "en": "Please ask about one of these topics and I will guide you step by step.",
                "ms": "Sila tanya tentang salah satu topik ini dan saya akan bantu langkah demi langkah.",
                "zh": "请围绕以上主题提问，我会一步一步协助您。",
            }[language],
        ),
    ]


def blocks_planning_intro(language: str) -> list[ChatBlock]:
    return blocks_simple_prompt(
        {"en": "Plan a route", "ms": "Rancang laluan", "zh": "规划路线"}[language],
        {
            "en": "Enter where you start and where you want to go, then choose when you travel.",
            "ms": "Masukkan tempat mula dan destinasi, kemudian pilih masa perjalanan.",
            "zh": "输入出发地和目的地，然后选择出行时间。",
        }[language],
        examples=[
            {
                "en": "ElderGo KL shows one clear recommended route.",
                "ms": "ElderGo KL menunjukkan satu laluan cadangan yang jelas.",
                "zh": "App 会显示一条清晰的推荐路线。",
            }[language]
        ],
    )


def parse_gemini_blocks_json(raw: str, language: str) -> list[ChatBlock] | None:
    """Parse and validate Gemini JSON block output."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    items: Any = data
    if isinstance(data, dict) and "blocks" in data:
        items = data["blocks"]
    if not isinstance(items, list):
        return None
    blocks: list[ChatBlock] = []
    for item in items[:8]:
        try:
            block = ChatBlock.model_validate(item)
        except ValidationError:
            continue
        if block.type == "sources" and block.links:
            block = ChatBlock(
                type="sources",
                text=block.text or _sources_heading(language),
                links=sanitize_source_links(block.links),
            )
            if not block.links:
                continue
        blocks.append(block)
    return blocks if blocks else None
