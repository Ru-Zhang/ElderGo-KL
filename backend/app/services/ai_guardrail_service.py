import re
import unicodedata

# ElderGo app feature topics (routes, stations, guides, preferences).
ELDERGO_TOPIC_KEYWORDS = {
    "eldergo",
    "route",
    "routes",
    "station",
    "stations",
    "accessibility",
    "accessible",
    "lift",
    "elevator",
    "ramp",
    "ticket",
    "tickets",
    "concession",
    "fare",
    "privacy",
    "preference",
    "preferences",
    "train",
    "mrt",
    "lrt",
    "ktm",
    "monorail",
    "bus",
    "wheelchair",
    "路线",
    "车站",
    "站点",
    "无障碍",
    "电梯",
    "坡道",
    "票",
    "车票",
    "优惠",
    "票价",
    "隐私",
    "偏好",
    "轮椅",
    "地铁",
    "轻轨",
    "巴士",
    "公交",
    "laluan",
    "stesen",
    "kebolehcapaian",
    "akses",
    "lif",
    "tiket",
    "tambang",
    "konsesi",
    "privasi",
    "warga emas",
    "kerusi roda",
    "tren",
    "bas",
    "help",
    "guide",
    "panduan",
}

# Broader travel / transit context (weather, commuting, getting around KL).
TRAVEL_RELATED_KEYWORDS = ELDERGO_TOPIC_KEYWORDS | {
    "weather",
    "rain",
    "raining",
    "hot",
    "storm",
    "umbrella",
    "temperature",
    "forecast",
    "cuaca",
    "hujan",
    "panas",
    "travel",
    "trip",
    "journey",
    "commute",
    "commuting",
    "going",
    "visit",
    "hospital",
    "clinic",
    "airport",
    "mall",
    "destination",
    "departure",
    "arrive",
    "walking",
    "walk",
    "transfer",
    "transfers",
    "platform",
    "exit",
    "entrance",
    "天气",
    "下雨",
    "出行",
    "旅行",
    "出发",
    "到达",
    "走路",
    "换乘",
    "pergi",
    "melawat",
    "cuaca",
    "berjalan",
    "pertukaran",
    "destinasi",
    "go",
    "get",
    "how",
    "where",
    "when",
    "why",
    "what",
    "which",
    "医院",
    "诊所",
    "商场",
    "机场",
}


def normalize_text(message: str) -> str:
    lowered = unicodedata.normalize("NFKC", message).lower()
    lowered = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _contains_keyword(normalized: str, keywords: set[str]) -> bool:
    if not normalized:
        return False
    return any(keyword in normalized for keyword in keywords)


def is_eldergo_topic(message: str) -> bool:
    return _contains_keyword(normalize_text(message), ELDERGO_TOPIC_KEYWORDS)


_ROUTE_TRAVEL_PATTERNS = (
    re.compile(r"\bfrom\s+[a-z0-9\u4e00-\u9fff]", re.I),
    re.compile(r"\bgo\s+from\b", re.I),
    re.compile(r"\bgo\s+to\b", re.I),
    re.compile(r"\bdari\s+[a-z0-9]", re.I),
    re.compile(r"从.+(到|去)"),
)


def is_travel_related(message: str) -> bool:
    from app.services.ai_exploratory_poi_service import is_exploratory_poi_message

    if is_exploratory_poi_message(message):
        return True
    if _contains_keyword(normalize_text(message), TRAVEL_RELATED_KEYWORDS):
        return True
    return any(pattern.search(message) for pattern in _ROUTE_TRAVEL_PATTERNS)


def is_in_scope(message: str) -> bool:
    # Backward-compatible alias used by tests and legacy imports.
    return is_travel_related(message)
