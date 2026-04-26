IN_SCOPE_KEYWORDS = {
    "route",
    "station",
    "accessibility",
    "accessible",
    "lift",
    "elevator",
    "ramp",
    "ticket",
    "concession",
    "fare",
    "privacy",
    "eldergo",
    "help",
    "share",
    "save",
    "train",
    "mrt",
    "lrt",
    "ktm",
    "monorail",
    "bus",
}


def is_in_scope(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in IN_SCOPE_KEYWORDS)
