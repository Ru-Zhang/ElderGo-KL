"""Build frontend seat-probability lookup JSON from ridership CSV and GTFS stops."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOPS_CSV = ROOT / "backend" / "csv_output" / "rapid_rail_data" / "stops.csv"
RIDERSHIP_CSV = ROOT / "backend" / "data" / "rapidkl_ridership_2024_2026_final_predicted_july_2026.csv"
OUT_DIR = ROOT / "frontend" / "src" / "data"


def normalize_code(code: str) -> str:
    code = code.strip().upper()
    match = re.match(r"^([A-Z]+)(\d+)$", code)
    if match:
        return f"{match.group(1)}{int(match.group(2))}"
    return code


def canonical_station_key(name: str) -> str:
    value = re.sub(r"\s*-\s*REDONE$", "", name.strip(), flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value)
    return value.upper()


def station_key_variants(name: str) -> set[str]:
    keys = {canonical_station_key(name)}
    if " - " in name:
        head = name.split(" - ", 1)[0].strip()
        if head:
            keys.add(canonical_station_key(head))
    return keys


def main() -> None:
    name_to_code: dict[str, str] = {}

    with STOPS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            stop_id = (row.get("stop_id") or "").strip()
            stop_name = (row.get("stop_name") or "").strip()
            if not stop_id or not stop_name:
                continue
            code = normalize_code(stop_id)
            for key in station_key_variants(stop_name):
                name_to_code.setdefault(key, code)

    seat_by_date_and_code: dict[str, float] = {}
    dates: list[str] = []

    with RIDERSHIP_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            date = (row.get("date") or "").strip()
            station_code = (row.get("station_code") or "").strip()
            station_name = (row.get("station_name") or "").strip()
            raw_prob = (row.get("seat_probability_percent") or "").strip()
            if not date or not station_code or not raw_prob:
                continue
            code = normalize_code(station_code)
            prob = round(float(raw_prob), 1)
            seat_by_date_and_code[f"{date}|{code}"] = prob
            dates.append(date)
            for key in station_key_variants(station_name):
                name_to_code.setdefault(key, code)

    if not dates:
        raise RuntimeError("No ridership rows were loaded.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "dateMin": min(dates),
        "dateMax": max(dates),
        "stationCount": len(name_to_code),
        "probabilityCount": len(seat_by_date_and_code),
    }

    (OUT_DIR / "stationNameToCode.json").write_text(
        json.dumps(name_to_code, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    (OUT_DIR / "seatByDateAndCode.json").write_text(
        json.dumps(seat_by_date_and_code, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    (OUT_DIR / "seatProbabilityMeta.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {len(name_to_code)} station name keys and {len(seat_by_date_and_code)} date/code probabilities.")
    print(f"Date range: {meta['dateMin']} .. {meta['dateMax']}")


if __name__ == "__main__":
    main()
