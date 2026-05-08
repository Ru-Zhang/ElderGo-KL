from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.services.database import get_connection

IntentType = Literal[
    "station_accessibility",
    "station_routes_info",
    "route_history_explain",
    "user_preferences",
    "help_static",
    "unknown",
]
ResponseSourceType = Literal["database", "static_help", "mixed", "fallback"]

HELP_KNOWLEDGE = {
    "en": {
        "buy_ticket": [
            "Use Touch 'n Go card for the fastest entry and exit.",
            "If buying a token: choose language, choose destination, pay cash, then collect token and change.",
            "Ticket info source is Rapid KL official website.",
        ],
        "concession": [
            "Malaysian citizens aged 60+ can get 50% fare discount on LRT, MRT, Monorail, and BRT.",
            "Bring original MyKad and apply at concession registration counter.",
            "Staff can process photo and card collection on the same day at supported counters.",
        ],
        "privacy": [
            "ElderGo does not track your phone GPS location.",
            "ElderGo does not keep your travel history after app is closed.",
            "ElderGo does not sell your data or show misleading ads.",
        ],
        "use_eldergo": [
            "Set travel preferences first, especially Accessibility First if needed.",
            "Plan route by entering origin and destination, then review one recommended route.",
            "Follow text steps and check accessibility notes before travel.",
        ],
    },
    "ms": {
        "buy_ticket": [
            "Gunakan kad Touch 'n Go untuk masuk dan keluar dengan lebih cepat.",
            "Jika beli token: pilih bahasa, pilih destinasi, bayar tunai, kemudian ambil token dan baki.",
            "Sumber maklumat tiket ialah laman web rasmi Rapid KL.",
        ],
        "concession": [
            "Warganegara Malaysia umur 60+ boleh dapat diskaun 50% untuk LRT, MRT, Monorail, dan BRT.",
            "Bawa MyKad asal dan mohon di kaunter pendaftaran konsesi.",
            "Kakitangan boleh urus gambar dan serahan kad pada hari sama di kaunter yang disokong.",
        ],
        "privacy": [
            "ElderGo tidak menjejak lokasi GPS telefon anda.",
            "ElderGo tidak menyimpan sejarah perjalanan selepas aplikasi ditutup.",
            "ElderGo tidak menjual data anda atau memaparkan iklan mengelirukan.",
        ],
        "use_eldergo": [
            "Tetapkan keutamaan perjalanan dahulu, terutama Accessibility First jika perlu.",
            "Rancang laluan dengan memasukkan lokasi mula dan destinasi, kemudian semak satu laluan cadangan.",
            "Ikut langkah teks dan semak nota aksesibiliti sebelum perjalanan.",
        ],
    },
    "zh": {
        "buy_ticket": [
            "建议使用 Touch 'n Go 卡，进出站更快。",
            "若买 token：先选语言、再选目的地、投币付款，最后拿 token 和找零。",
            "票务说明来源为 Rapid KL 官方网站。",
        ],
        "concession": [
            "马来西亚 60 岁及以上公民可享 LRT/MRT/Monorail/BRT 约 50% 折扣。",
            "请携带原件 MyKad，到优惠登记柜台申请。",
            "支持的柜台可当天拍照并领取优惠卡。",
        ],
        "privacy": [
            "ElderGo 不追踪你的手机 GPS 位置。",
            "关闭应用后不会保留你的出行历史。",
            "不会出售你的数据，也不会展示误导性广告。",
        ],
        "use_eldergo": [
            "先设置出行偏好，尤其是需要时开启无障碍优先。",
            "输入起点和终点后规划路线，再查看推荐路线。",
            "出发前按文字步骤行进，并查看无障碍提示。",
        ],
    },
}

HELP_KEYWORDS: dict[str, tuple[str, ...]] = {
    "buy_ticket": ("buy ticket", "ticket", "token", "touch n go", "车票", "买票", "tiket"),
    "concession": ("concession", "discount", "senior", "优惠", "折扣", "konsesi", "diskaun", "warga emas"),
    "privacy": ("privacy", "data", "gps", "隐私", "定位", "privasi"),
    "use_eldergo": ("use eldergo", "how to use", "如何使用", "cara guna", "cara menggunakan"),
}


@dataclass
class GroundedContext:
    intent: IntentType
    grounded: bool
    response_source: ResponseSourceType
    used_data_keys: list[str]
    facts: list[str]


def _detect_language(message: str) -> str:
    if any("\u4e00" <= ch <= "\u9fff" for ch in message):
        return "zh"

    lowered = f" {message.lower()} "
    if any(hint in lowered for hint in (" saya ", " dan ", " bagaimana ", " stesen ", " tiket ", " boleh ")):
        return "ms"
    return "en"


def _intent_from_message(message: str) -> IntentType:
    lowered = message.lower()
    if any(token in lowered for token in ("buy ticket", "token", "touch", "concession", "privacy", "use eldergo")):
        return "help_static"
    if any(token in lowered for token in ("优惠", "买票", "隐私", "如何使用", "konsesi", "privasi", "tiket")):
        return "help_static"
    if any(token in lowered for token in ("current route", "route step", "last route", "路线步骤", "laluan")):
        return "route_history_explain"
    if any(token in lowered for token in ("preference", "font size", "language", "偏好", "设置", "keutamaan")):
        return "user_preferences"
    if any(token in lowered for token in ("accessibility", "wheelchair", "lift", "elevator", "无障碍", "电梯", "akses")):
        return "station_accessibility"
    if any(token in lowered for token in ("station", "line", "route", "站", "线路", "stesen")):
        return "station_routes_info"
    return "unknown"


def _extract_help_key(message: str) -> str | None:
    lowered = message.lower()
    for key, keywords in HELP_KEYWORDS.items():
        if any(token in lowered for token in keywords):
            return key
    return None


def _help_context(message: str) -> GroundedContext:
    language = _detect_language(message)
    key = _extract_help_key(message)
    if not key:
        return GroundedContext(
            intent="help_static",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        )

    facts = HELP_KNOWLEDGE[language].get(key, HELP_KNOWLEDGE["en"][key])
    return GroundedContext(
        intent="help_static",
        grounded=True,
        response_source="static_help",
        used_data_keys=[f"help.{key}"],
        facts=facts,
    )


def _station_context(message: str, selected_location_id: str | None, accessibility_focus: bool) -> GroundedContext:
    try:
        with get_connection() as conn:
            row = None
            if selected_location_id:
                row = conn.execute(
                    """
                    SELECT location_id, display_name, accessibility_status, confidence
                    FROM searchable_locations
                    WHERE location_id = %(location_id)s
                    """,
                    {"location_id": selected_location_id},
                ).fetchone()

            if row is None:
                query = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", message).strip()
                row = conn.execute(
                    """
                    SELECT location_id, display_name, accessibility_status, confidence
                    FROM searchable_locations
                    WHERE location_type = 'rail_station'
                      AND display_name ILIKE %(like_query)s
                    ORDER BY similarity(display_name, %(query)s) DESC, display_name
                    LIMIT 1
                    """,
                    {"query": query or message, "like_query": f"%{query or message}%"},
                ).fetchone()

            if row is None:
                return GroundedContext(
                    intent="station_accessibility" if accessibility_focus else "station_routes_info",
                    grounded=False,
                    response_source="fallback",
                    used_data_keys=[],
                    facts=[],
                )

            facts = [
                f"Station: {row['display_name']}",
                f"Accessibility status: {row.get('accessibility_status') or 'unknown'}",
                f"Data confidence: {row.get('confidence') or 'unknown'}",
            ]
            used_keys = ["searchable_locations.display_name", "searchable_locations.accessibility_status"]

            if accessibility_focus:
                nearby = conn.execute(
                    """
                    SELECT
                        BOOL_OR(LOWER(COALESCE(point.wheelchair, '')) IN ('yes', 'limited')) AS wheelchair_access,
                        BOOL_OR(LOWER(COALESCE(point.shelter, '')) IN ('yes', 'limited')) AS shelter,
                        BOOL_OR(LOWER(COALESCE(point.covered, '')) IN ('yes', 'limited')) AS covered
                    FROM station_group_members member
                    JOIN rail_stations station ON station.station_id = member.station_id
                    JOIN accessibility_points point
                      ON station.geom IS NOT NULL
                     AND point.geom IS NOT NULL
                     AND ST_DWithin(station.geom::geography, point.geom::geography, 50)
                    WHERE member.station_group_id = %(station_group_id)s
                    """,
                    {"station_group_id": row["location_id"]},
                ).fetchone()
                if nearby:
                    facts.append(
                        "Nearby facilities: wheelchair=%s, shelter=%s, covered=%s"
                        % (
                            "yes" if nearby.get("wheelchair_access") else "no/unknown",
                            "yes" if nearby.get("shelter") else "no/unknown",
                            "yes" if nearby.get("covered") else "no/unknown",
                        )
                    )
                    used_keys.append("accessibility_points.*")
            else:
                routes = conn.execute(
                    """
                    SELECT DISTINCT route.route_short_name AS route_name
                    FROM station_group_members member
                    JOIN rail_station_routes station_route ON station_route.station_id = member.station_id
                    JOIN rail_routes route ON route.route_id = station_route.route_id
                    WHERE member.station_group_id = %(station_group_id)s
                      AND route.route_short_name IS NOT NULL
                    ORDER BY route.route_short_name
                    LIMIT 6
                    """,
                    {"station_group_id": row["location_id"]},
                ).fetchall()
                route_names = [item["route_name"] for item in routes if item.get("route_name")]
                if route_names:
                    facts.append(f"Available lines: {', '.join(route_names)}")
                    used_keys.append("rail_routes.route_short_name")

            return GroundedContext(
                intent="station_accessibility" if accessibility_focus else "station_routes_info",
                grounded=True,
                response_source="database",
                used_data_keys=used_keys,
                facts=facts,
            )
    except Exception:
        return GroundedContext(
            intent="station_accessibility" if accessibility_focus else "station_routes_info",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        )


def _route_history_context(current_route_id: str | None) -> GroundedContext:
    if not current_route_id:
        return GroundedContext(
            intent="route_history_explain",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        )
    try:
        with get_connection() as conn:
            route = conn.execute(
                """
                SELECT
                    recommended_route_id::text AS recommended_route_id,
                    total_duration_min,
                    walking_distance_m,
                    transfer_count,
                    summary_text
                FROM recommended_routes
                WHERE recommended_route_id::text = %(route_id)s
                """,
                {"route_id": current_route_id},
            ).fetchone()
            if route is None:
                return GroundedContext(
                    intent="route_history_explain",
                    grounded=False,
                    response_source="fallback",
                    used_data_keys=[],
                    facts=[],
                )

            steps = conn.execute(
                """
                SELECT step_order, travel_mode, instruction_text, duration_min
                FROM route_steps
                WHERE recommended_route_id::text = %(route_id)s
                ORDER BY step_order
                LIMIT 5
                """,
                {"route_id": current_route_id},
            ).fetchall()
            facts = [
                f"Route duration minutes: {route.get('total_duration_min')}",
                f"Route walking distance meters: {route.get('walking_distance_m')}",
                f"Route transfer count: {route.get('transfer_count')}",
            ]
            for item in steps:
                facts.append(
                    f"Step {item['step_order']}: {item.get('travel_mode')}, {item.get('instruction_text')}, {item.get('duration_min')} min"
                )
            return GroundedContext(
                intent="route_history_explain",
                grounded=True,
                response_source="database",
                used_data_keys=["recommended_routes.*", "route_steps.*"],
                facts=facts,
            )
    except Exception:
        return GroundedContext(
            intent="route_history_explain",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        )


def _user_preferences_context(anonymous_user_id: str | None) -> GroundedContext:
    if not anonymous_user_id:
        return GroundedContext(
            intent="user_preferences",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        )
    try:
        with get_connection() as conn:
            ui_row = conn.execute(
                """
                SELECT language_code, font_size_mode, onboarding_completed
                FROM user_ui_settings
                WHERE anonymous_user_id::text = %(anonymous_user_id)s
                """,
                {"anonymous_user_id": anonymous_user_id},
            ).fetchone()
            pref_row = conn.execute(
                """
                SELECT accessibility_first, less_walking, fewer_transfers
                FROM user_travel_preferences
                WHERE anonymous_user_id::text = %(anonymous_user_id)s
                """,
                {"anonymous_user_id": anonymous_user_id},
            ).fetchone()
            if ui_row is None and pref_row is None:
                return GroundedContext(
                    intent="user_preferences",
                    grounded=False,
                    response_source="fallback",
                    used_data_keys=[],
                    facts=[],
                )

            facts: list[str] = []
            if ui_row is not None:
                facts.extend(
                    [
                        f"UI language code: {ui_row.get('language_code') or 'en'}",
                        f"UI font size mode: {ui_row.get('font_size_mode') or 'standard'}",
                        f"Onboarding completed: {bool(ui_row.get('onboarding_completed'))}",
                    ]
                )
            if pref_row is not None:
                facts.extend(
                    [
                        f"Accessibility first: {bool(pref_row.get('accessibility_first'))}",
                        f"Least walking: {bool(pref_row.get('less_walking'))}",
                        f"Fewest transfers: {bool(pref_row.get('fewer_transfers'))}",
                    ]
                )
            return GroundedContext(
                intent="user_preferences",
                grounded=True,
                response_source="database",
                used_data_keys=["user_ui_settings.*", "user_travel_preferences.*"],
                facts=facts,
            )
    except Exception:
        return GroundedContext(
            intent="user_preferences",
            grounded=False,
            response_source="fallback",
            used_data_keys=[],
            facts=[],
        )


def build_grounded_context(
    *,
    message: str,
    current_route_id: str | None,
    selected_location_id: str | None,
    anonymous_user_id: str | None,
) -> GroundedContext:
    intent = _intent_from_message(message)
    if intent == "help_static":
        return _help_context(message)
    if intent == "station_accessibility":
        return _station_context(message, selected_location_id, accessibility_focus=True)
    if intent == "station_routes_info":
        return _station_context(message, selected_location_id, accessibility_focus=False)
    if intent == "route_history_explain":
        return _route_history_context(current_route_id)
    if intent == "user_preferences":
        return _user_preferences_context(anonymous_user_id)
    return GroundedContext(
        intent="unknown",
        grounded=False,
        response_source="fallback",
        used_data_keys=[],
        facts=[],
    )

