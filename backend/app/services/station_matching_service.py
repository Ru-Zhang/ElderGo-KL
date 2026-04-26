def normalize_station_name(name: str) -> str:
    return " ".join(name.lower().strip().split())
