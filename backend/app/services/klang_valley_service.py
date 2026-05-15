"""Klang Valley geographic scope checks for chatbot and routing."""

from app.schemas.places import PlaceDetail

# Approximate bounding box for Klang Valley (KL + greater Selangor corridor).
KV_LAT_MIN = 2.70
KV_LAT_MAX = 3.55
KV_LON_MIN = 100.95
KV_LON_MAX = 101.95

KV_REJECT_MESSAGES = {
    "en": (
        "ElderGo KL only supports travel within the Klang Valley.\n"
        "- Please choose a start and destination in Kuala Lumpur or Selangor.\n"
        "- Areas outside Klang Valley are not supported yet."
    ),
    "ms": (
        "ElderGo KL hanya menyokong perjalanan dalam Lembah Klang.\n"
        "- Sila pilih tempat mula dan destinasi di Kuala Lumpur atau Selangor.\n"
        "- Kawasan di luar Lembah Klang belum disokong."
    ),
    "zh": (
        "ElderGo KL 仅支持巴生谷（Klang Valley）内的出行。\n"
        "- 请选择吉隆坡或雪兰莪范围内的出发地和目的地。\n"
        "- 巴生谷以外的地区暂不支持。"
    ),
}


def is_in_klang_valley(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    return KV_LAT_MIN <= lat <= KV_LAT_MAX and KV_LON_MIN <= lon <= KV_LON_MAX


def reject_outside_kv_message(language: str) -> str:
    return KV_REJECT_MESSAGES.get(language, KV_REJECT_MESSAGES["en"])


def place_detail_in_kv(place: PlaceDetail) -> bool:
    return is_in_klang_valley(place.lat, place.lon)
