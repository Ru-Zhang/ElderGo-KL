"""Build human-readable transit line direction from Google Directions transit_details."""

from __future__ import annotations

import re

# Terminus pairs sourced from rapid_rail_data/routes.csv (route_desc).
_LINE_TERMINI: list[tuple[tuple[str, ...], str, str]] = [
    (("kelana jaya", "kjl"), "Gombak", "Putra Heights"),
    (("ampang line", "agl", "lrt ampang"), "Ampang", "Sentul Timur"),
    (("sri petaling", "spl"), "Putra Heights", "Sentul Timur"),
    (("kajang line", "kgl", "mrt kajang"), "Kwasa Damansara", "Kajang"),
    (("putrajaya line", "pyl", "mrt putrajaya"), "Putrajaya", "Kwasa Damansara"),
    (("monorel", "monorail", "mrl", "kl monorail"), "Titiwangsa", "KL Sentral"),
    (("brt sunway", "brt", "sunway line"), "Sunway-Setia Jaya", "USJ 7"),
]

# Canonical terminus labels and the stop/headsign aliases that refer to each end.
_TERMINUS_ALIASES: dict[str, tuple[str, ...]] = {
    "Gombak": ("gombak",),
    "Putra Heights": ("putra height", "putra heights"),
    "Ampang": ("ampang",),
    "Sentul Timur": ("sentul timur", "sentul"),
    "Kwasa Damansara": ("kwasa damansara",),
    "Kajang": ("kajang",),
    "Putrajaya": ("putrajaya", "putrajaya sentral"),
    "Titiwangsa": ("titiwangsa",),
    "KL Sentral": ("kl sentral", "kl sentral"),
    "Sunway-Setia Jaya": (
        "sunway-setia jaya",
        "setia jaya",
        "sunway setia jaya",
        "sunu-monash",
        "sunu monash",
        "sunway university",
    ),
    "USJ 7": ("usj 7", "usj7", "stesen brt usj7"),
}


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    cleaned = re.sub(r"^stesen\s+(brt|lrt|mrt)?\s*", "", cleaned)
    return cleaned


def _names_match(left: str, right: str) -> bool:
    a = _normalize(left)
    b = _normalize(right)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    for aliases in _TERMINUS_ALIASES.values():
        if a in aliases and b in aliases:
            return True
        if a in aliases and any(alias in b or b in alias for alias in aliases):
            return True
        if b in aliases and any(alias in a or a in alias for alias in aliases):
            return True
    return False


def _resolve_terminus(label: str, name: str | None) -> bool:
    if not name:
        return False
    if _names_match(name, label):
        return True
    aliases = _TERMINUS_ALIASES.get(label, ())
    normalized = _normalize(name)
    return any(alias in normalized or normalized in alias for alias in aliases)


def _line_tokens(transit: dict) -> str:
    line = transit.get("line", {})
    vehicle = line.get("vehicle", {})
    parts = [
        line.get("name"),
        line.get("short_name"),
        vehicle.get("name"),
        vehicle.get("type"),
    ]
    return _normalize(" ".join(part for part in parts if part))


def _match_profile(transit: dict) -> tuple[str, str] | None:
    tokens = _line_tokens(transit)
    if not tokens:
        return None
    for patterns, terminus_a, terminus_b in _LINE_TERMINI:
        if any(pattern in tokens for pattern in patterns):
            return terminus_a, terminus_b
    return None


def _direction_from_stops(
    transit: dict,
    terminus_a: str,
    terminus_b: str,
) -> tuple[str, str] | None:
    departure = transit.get("departure_stop", {}).get("name")
    arrival = transit.get("arrival_stop", {}).get("name")
    if not departure or not arrival:
        return None

    dep_is_a = _resolve_terminus(terminus_a, departure)
    dep_is_b = _resolve_terminus(terminus_b, departure)
    arr_is_a = _resolve_terminus(terminus_a, arrival)
    arr_is_b = _resolve_terminus(terminus_b, arrival)

    if dep_is_a and arr_is_b:
        return terminus_a, terminus_b
    if dep_is_b and arr_is_a:
        return terminus_b, terminus_a
    return None


def _direction_from_headsign(
    headsign: str,
    terminus_a: str,
    terminus_b: str,
) -> tuple[str, str] | None:
    if _resolve_terminus(terminus_b, headsign):
        return terminus_a, terminus_b
    if _resolve_terminus(terminus_a, headsign):
        return terminus_b, terminus_a
    return None


def build_transit_line_direction(transit: dict | None) -> tuple[str, str] | None:
    """
    Return (from_terminus, to_terminus) for this transit leg.

    Stop names are preferred over headsign because Google may report the line
    terminus as headsign even when the passenger boards mid-route (e.g. BRT at
    USJ 7 heading towards SunU-Monash).
    """
    if not transit:
        return None

    profile = _match_profile(transit)
    if not profile:
        return None

    terminus_a, terminus_b = profile

    stop_direction = _direction_from_stops(transit, terminus_a, terminus_b)
    if stop_direction:
        return stop_direction

    headsign = (transit.get("headsign") or "").strip()
    if not headsign:
        return None

    return _direction_from_headsign(headsign, terminus_a, terminus_b)
