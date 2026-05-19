"""Attach curated step photos from backend/data/route_*.csv by Monash corridor segment."""

from __future__ import annotations

from typing import TypedDict

from app.services.curated_corridor_policy import (
    CANONICAL_CORRIDOR_ROUTE_KEY,
    csv_step_for_google_step,
    detect_curated_profile,
    should_use_curated_route_csv,
)
from app.services.route_station_images_service import (
    RouteStationImage,
    get_route_step_images,
)


class RouteStationImageRef(TypedDict):
    path: str
    caption: str


def is_curated_corridor_route(origin_name: str, destination_name: str) -> bool:
    return should_use_curated_route_csv(origin_name, destination_name)


def reload_segment_image_templates_cache() -> None:
    """No-op: templates CSV replaced by explicit segment mapping in curated_corridor_policy."""


def _to_refs(images: list[RouteStationImage]) -> list[RouteStationImageRef]:
    return [{"path": image["path"], "caption": image["caption"]} for image in images]


def resolve_route_step_images(
    google_steps: list[dict],
    origin_name: str,
    destination_name: str,
) -> dict[int, list[RouteStationImageRef]]:
    profile = detect_curated_profile(
        origin_name,
        destination_name,
        google_steps=google_steps,
    )
    if profile is None:
        return {}

    resolved: dict[int, list[RouteStationImageRef]] = {}
    previous_paths: set[str] = set()

    for index, step in enumerate(google_steps):
        step_number = index + 1
        csv_step = csv_step_for_google_step(
            step,
            profile,
            origin_name=origin_name,
            destination_name=destination_name,
        )
        if csv_step is None:
            resolved[step_number] = []
            continue

        images = _to_refs(
            get_route_step_images(CANONICAL_CORRIDOR_ROUTE_KEY, csv_step),
        )
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
