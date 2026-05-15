"""Parse MRT-style station hours_summary strings into structured sections."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ConditionalTime:
    time: str
    condition: str = ""


@dataclass
class LastTrainDest:
    to: str
    values: list[ConditionalTime] = field(default_factory=list)


@dataclass
class ParsedHours:
    open: list[ConditionalTime] = field(default_factory=list)
    close: list[ConditionalTime] = field(default_factory=list)
    last_trains: list[LastTrainDest] = field(default_factory=list)
    other: list[str] = field(default_factory=list)


def parse_hours_summary(raw: str | None) -> ParsedHours | None:
    if not raw or not raw.strip():
        return None

    result = ParsedHours()
    lines = [line.strip() for line in raw.replace("\r\n", "\n").split("\n") if line.strip()]
    if not lines:
        return None

    for line in lines:
        colon = line.find(":")
        if colon < 0:
            result.other.append(line)
            continue
        key = line[:colon].strip()
        value = line[colon + 1 :].strip()

        if re.match(r"^station open$", key, re.I):
            result.open.extend(_split_condition_time(value))
        elif re.match(r"^station closed$", key, re.I):
            result.close.extend(_split_condition_time(value))
        elif m := re.match(r"^last train to\s*(.+)$", key, re.I):
            dest = m.group(1).strip()
            result.last_trains.append(LastTrainDest(to=dest, values=_split_condition_time(value)))
        elif re.match(r"^last train$", key, re.I):
            result.other.append(f"{key}: {value}")
        else:
            result.other.append(line)

    if not (result.open or result.close or result.last_trains or result.other):
        return None
    return result


def _split_condition_time(raw: str) -> list[ConditionalTime]:
    entries: list[ConditionalTime] = []
    for segment in re.split(r"\s*/\s*", raw):
        trimmed = segment.strip()
        if not trimmed:
            continue
        m = re.match(r"^(.+?)\s*\((.+?)\)\s*$", trimmed)
        if m:
            entries.append(
                ConditionalTime(
                    time=_normalize_time(m.group(1).strip()),
                    condition=_normalize_condition(m.group(2).strip()),
                )
            )
        else:
            entries.append(ConditionalTime(time=_normalize_time(trimmed)))
    return [e for e in entries if e.time]


def _normalize_time(raw: str) -> str:
    return re.sub(r"\b(am|pm)\b", lambda m: m.group(1).upper(), re.sub(r"\s+", " ", raw)).strip()


def _normalize_condition(raw: str) -> str:
    cleaned = re.sub(r"\s+", " ", raw).strip()
    cleaned = re.sub(r"\bSunday\b", "Sun", cleaned, flags=re.I)
    cleaned = re.sub(r"\bMonday\b", "Mon", cleaned, flags=re.I)
    return cleaned
