def normalize_station_name(name: str) -> str:
    # Canonicalize spacing/case so fuzzy matching compares stable station keys.
    return " ".join(name.lower().strip().split())
