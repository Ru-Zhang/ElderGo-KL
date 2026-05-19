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
    "discount",
    "discounts",
    "cheaper",
    "fare",
    "fares",
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
    "diskaun",
    "discount",
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
    "超市",
    "学校",
    "咖啡厅",
    "商场",
    "clinic",
    "cafe",
    "supermarket",
    "school",
    "机场",
}


def normalize_text(message: str) -> str:
    lowered = unicodedata.normalize("NFKC", message).lower()
    lowered = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


_NON_TRAVEL_TOPIC_PATTERNS = (
    re.compile(
        r"\b(?:cook|cooking|recipe|fried\s+rice|boil\s+rice|bake|food\s+recipe)\b",
        re.I,
    ),
    re.compile(r"(?:做饭|做菜|煮饭|食谱|炒菜)"),
)


def _contains_keyword(normalized: str, keywords: set[str]) -> bool:
    if not normalized:
        return False
    for keyword in keywords:
        if re.search(r"[\u4e00-\u9fff]", keyword):
            if keyword in normalized:
                return True
        elif len(keyword) <= 4:
            if re.search(rf"\b{re.escape(keyword)}\b", normalized):
                return True
        elif keyword in normalized:
            return True
    return False


def is_eldergo_topic(message: str) -> bool:
    return _contains_keyword(normalize_text(message), ELDERGO_TOPIC_KEYWORDS)


_ROUTE_TRAVEL_PATTERNS = (
    re.compile(r"\bfrom\s+[a-z0-9\u4e00-\u9fff]", re.I),
    re.compile(r"\bgo\s+from\b", re.I),
    re.compile(r"\bgo\s+to\b", re.I),
    re.compile(r"\bdari\s+[a-z0-9]", re.I),
    re.compile(r"从.+(到|去)"),
    # Bare "A to B" / "A ke B" without "from" or "go" (e.g. monash to klcc at 1pm).
    re.compile(
        r"^(?!(?:how|what|where|when|why|who)\b).+\s+to\s+.+$",
        re.I,
    ),
    re.compile(r"^.+\s+ke\s+.+$", re.I),
)


def is_travel_related(message: str) -> bool:
    from app.services.ai_exploratory_poi_service import is_exploratory_poi_message
    from app.services.ai_route_parse_service import message_has_plan_route_endpoints

    if any(pattern.search(message) for pattern in _NON_TRAVEL_TOPIC_PATTERNS):
        if not message_has_plan_route_endpoints(message):
            from app.services.ai_route_sentence_service import extract_route_endpoints

            origin, destination = extract_route_endpoints(message)
            if not origin and not destination:
                return False

    if is_exploratory_poi_message(message):
        return True
    if message_has_plan_route_endpoints(message):
        return True
    from app.services.ai_route_sentence_service import extract_route_endpoints

    origin, destination = extract_route_endpoints(message)
    if origin or destination:
        return True
    if _contains_keyword(normalize_text(message), TRAVEL_RELATED_KEYWORDS):
        return True
    return any(pattern.search(message.strip()) for pattern in _ROUTE_TRAVEL_PATTERNS)


def is_in_scope(message: str) -> bool:
    # Backward-compatible alias used by tests and legacy imports.
    return is_travel_related(message)
