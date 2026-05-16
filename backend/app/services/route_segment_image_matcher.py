"""Match curated step photos by OD key or reusable corridor segment templates."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import TypedDict

from app.core.paths import ROUTE_SEGMENT_IMAGE_TEMPLATES_CSV
from app.services.route_station_images_service import (
    RouteStationImage,
    get_route_step_images,
    normalize_route_key,
)
from app.services.transit_direction_service import build_transit_line_direction

_MATCH_THRESHOLD = 5
CANONICAL_CORRIDOR_ROUTE_KEY = "klcc|monash university malaysia"


class RouteStationImageRef(TypedDict):
    path: str
    caption: str


@dataclass(frozen=True)
class SegmentTemplate:
    segment_id: str
    source_route_key: str
    source_step_number: int
    from_patterns: tuple[str, ...]
    to_patterns: tuple[str, ...]
    line_patterns: tuple[str, ...]
    vehicle_type: str | None
    instruction_patterns: tuple[str, ...]
    expected_direction_from: tuple[str, ...]
    expected_direction_to: tuple[str, ...]


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def _split_patterns(value: str | None) -> tuple[str, ...]:
    if not value or not value.strip():
        return ()
    return tuple(part.strip().lower() for part in value.split("|") if part.strip())


def is_monash_corridor_destination(destination_name: str) -> bool:
    return "monash" in _normalize_text(destination_name)


def _is_canonical_corridor_od(origin_name: str, destination_name: str) -> bool:
    route_key = f"{normalize_route_key(origin_name)}|{normalize_route_key(destination_name)}"
    return route_key == CANONICAL_CORRIDOR_ROUTE_KEY


def _read_templates(csv_path) -> list[SegmentTemplate]:
    if not csv_path.is_file():
        return []
    templates: list[SegmentTemplate] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            segment_id = (row.get("segment_id") or "").strip()
            source_route_key = normalize_route_key(row.get("source_route_key") or "")
            try:
                source_step_number = int((row.get("source_step_number") or "0").strip())
            except ValueError:
                continue
            if not segment_id or not source_route_key or source_step_number < 1:
                continue
            vehicle = (row.get("vehicle_type") or "").strip().upper() or None
            templates.append(
                SegmentTemplate(
                    segment_id=segment_id,
                    source_route_key=source_route_key,
                    source_step_number=source_step_number,
                    from_patterns=_split_patterns(row.get("from_station_pattern")),
                    to_patterns=_split_patterns(row.get("to_station_pattern")),
                    line_patterns=_split_patterns(row.get("transit_line_pattern")),
                    vehicle_type=vehicle,
                    instruction_patterns=_split_patterns(row.get("instruction_pattern")),
                    expected_direction_from=_split_patterns(row.get("expected_direction_from")),
                    expected_direction_to=_split_patterns(row.get("expected_direction_to")),
                )
            )
    return templates


@lru_cache
def _load_templates() -> tuple[SegmentTemplate, ...]:
    return tuple(_read_templates(ROUTE_SEGMENT_IMAGE_TEMPLATES_CSV))


def reload_segment_image_templates_cache() -> None:
    _load_templates.cache_clear()


def _pattern_hits(patterns: tuple[str, ...], *haystacks: str) -> int:
    if not patterns:
        return 0
    combined = " ".join(h for h in haystacks if h)
    if not combined:
        return 0
    return sum(1 for pattern in patterns if pattern in combined)


def _terminus_matches(patterns: tuple[str, ...], terminus: str) -> bool:
    if not patterns:
        return True
    normalized = _normalize_text(terminus)
    if not normalized:
        return False
    for pattern in patterns:
        if pattern in normalized or normalized in pattern:
            return True
    return False


def _direction_matches(template: SegmentTemplate, step: dict) -> bool:
    if not template.expected_direction_from and not template.expected_direction_to:
        return True

    mode = (step.get("travel_mode") or "").upper()
    if mode != "TRANSIT":
        return False

    transit = step.get("transit_details") or {}
    direction = build_transit_line_direction(transit)
    if not direction:
        return False

    from_term, to_term = direction
    if template.expected_direction_from and not _terminus_matches(
        template.expected_direction_from, from_term
    ):
        return False
    if template.expected_direction_to and not _terminus_matches(template.expected_direction_to, to_term):
        return False
    return True


def _score_template(template: SegmentTemplate, step: dict) -> int:
    if not _direction_matches(template, step):
        return 0

    mode = (step.get("travel_mode") or "").upper()
    transit = step.get("transit_details") or {}
    line = transit.get("line") or {}
    vehicle = (line.get("vehicle") or {}).get("type") or ""
    from_station = _normalize_text(transit.get("departure_stop", {}).get("name"))
    to_station = _normalize_text(transit.get("arrival_stop", {}).get("name"))
    instruction = _normalize_text(step.get("html_instructions"))
    line_name = _normalize_text(line.get("short_name") or line.get("name"))

    if mode == "WALKING":
        if template.vehicle_type:
            return 0
        score = _pattern_hits(template.instruction_patterns, instruction)
        score += _pattern_hits(template.from_patterns, from_station, instruction) * 2
        score += _pattern_hits(template.to_patterns, to_station, instruction) * 2
        if score < 2:
            return 0
        return score

    if mode != "TRANSIT":
        return 0

    if template.vehicle_type:
        if template.vehicle_type != vehicle.upper():
            return 0
    elif vehicle:
        return 0

    from_hits = _pattern_hits(template.from_patterns, from_station, instruction)
    to_hits = _pattern_hits(template.to_patterns, to_station, instruction)
    line_hits = _pattern_hits(template.line_patterns, line_name, instruction)

    if template.from_patterns or template.to_patterns:
        if from_hits == 0 and to_hits == 0:
            return 0

    if template.line_patterns and line_hits == 0:
        return 0

    score = 0
    if template.vehicle_type and template.vehicle_type == vehicle.upper():
        score += 3
    score += from_hits * 2
    score += to_hits * 2
    score += line_hits
    score += _pattern_hits(template.instruction_patterns, instruction)
    return score


def _to_refs(images: list[RouteStationImage]) -> list[RouteStationImageRef]:
    return [{"path": image["path"], "caption": image["caption"]} for image in images]


def _exact_od_images(origin_name: str, destination_name: str, step_number: int) -> list[RouteStationImage]:
    if not _is_canonical_corridor_od(origin_name, destination_name):
        return []
    return get_route_step_images(CANONICAL_CORRIDOR_ROUTE_KEY, step_number)


def match_step_images(
    step: dict,
    step_number: int,
    origin_name: str,
    destination_name: str,
) -> list[RouteStationImageRef]:
    if not is_monash_corridor_destination(destination_name):
        return []

    exact = _exact_od_images(origin_name, destination_name, step_number)
    if exact:
        return _to_refs(exact)

    best_template: SegmentTemplate | None = None
    best_score = 0
    for template in _load_templates():
        score = _score_template(template, step)
        if score > best_score:
            best_score = score
            best_template = template

    if best_template is None or best_score < _MATCH_THRESHOLD:
        return []

    images = get_route_step_images(best_template.source_route_key, best_template.source_step_number)
    return _to_refs(images)


def resolve_route_step_images(
    google_steps: list[dict],
    origin_name: str,
    destination_name: str,
) -> dict[int, list[RouteStationImageRef]]:
    resolved: dict[int, list[RouteStationImageRef]] = {}
    previous_paths: set[str] = set()

    for index, step in enumerate(google_steps):
        step_number = index + 1
        images = match_step_images(step, step_number, origin_name, destination_name)
        if not images:
            resolved[step_number] = []
            continue

        deduped: list[RouteStationImageRef] = []
        for image in images:
            path = image["path"]
            if path in previous_paths and len(images) > 1:
                continue
            deduped.append(image)
        if not deduped and images:
            deduped = [images[0]]

        resolved[step_number] = deduped
        previous_paths = {image["path"] for image in deduped}

    return resolved
