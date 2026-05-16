import json
from typing import Literal

from pydantic import BaseModel, Field, field_validator


PreferenceFactor = Literal["accessibility", "walk", "transfers"]
DEFAULT_PRIORITY_ORDER: list[PreferenceFactor] = ["accessibility", "walk", "transfers"]


class TravelPreferences(BaseModel):
    # Defaults keep unconfigured planning aligned with Google Maps fastest transit.
    accessibility_first: bool = False
    least_walk: bool = False
    fewest_transfers: bool = False
    priority_order: list[PreferenceFactor] = Field(default_factory=lambda: list(DEFAULT_PRIORITY_ORDER))

    @field_validator("priority_order", mode="before")
    @classmethod
    def normalize_priority_order(cls, value) -> list[PreferenceFactor]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = None
        if not isinstance(value, list):
            return list(DEFAULT_PRIORITY_ORDER)

        normalized: list[PreferenceFactor] = []
        for item in value:
            if item in DEFAULT_PRIORITY_ORDER and item not in normalized:
                normalized.append(item)

        for factor in DEFAULT_PRIORITY_ORDER:
            if factor not in normalized:
                normalized.append(factor)

        return normalized
