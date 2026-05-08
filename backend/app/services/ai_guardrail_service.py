import re
import unicodedata

# Keep multilingual scope terms grouped by product topics so updates remain
# auditable as ElderGo support coverage expands.
IN_SCOPE_KEYWORDS = {
    # EN
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
    "train",
    "mrt",
    "lrt",
    "ktm",
    "monorail",
    "bus",
    "wheelchair",
    # ZH
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
    "轮椅",
    "地铁",
    "轻轨",
    "巴士",
    "公交",
    # MS
    "laluan",
    "stesen",
    "kebolehcapaian",
    "akses",
    "lif",
    "ramp",
    "tiket",
    "tambang",
    "konsesi",
    "privasi",
    "warga emas",
    "kerusi roda",
    "tren",
    "bas",
}


def normalize_text(message: str) -> str:
    lowered = unicodedata.normalize("NFKC", message).lower()
    lowered = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def is_in_scope(message: str) -> bool:
    normalized = normalize_text(message)
    if not normalized:
        return False
    return any(keyword in normalized for keyword in IN_SCOPE_KEYWORDS)
