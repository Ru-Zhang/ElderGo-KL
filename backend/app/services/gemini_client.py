"""Shared Gemini API client with key pool rotation."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()

GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)

# Klang Valley centre for Maps grounding bias
KV_GROUNDING_LAT = 3.1390
KV_GROUNDING_LON = 101.6869

MAPS_GROUNDING_LANGUAGE = {
    "en": "en_US",
    "ms": "ms_MY",
    "zh": "zh_CN",
}


class GeminiKeyPool:
    def __init__(self) -> None:
        self._lock = Lock()
        self._exhausted_until: dict[str, datetime] = {}
        self._cursor = 0

    @staticmethod
    def _local_day_end_utc() -> datetime:
        tz = timezone(timedelta(hours=8))
        now_local = datetime.now(tz=tz)
        next_day_start = datetime.combine(
            (now_local + timedelta(days=1)).date(),
            datetime.min.time(),
            tzinfo=tz,
        )
        return next_day_start.astimezone(timezone.utc)

    @staticmethod
    def is_rate_limit_error(exc: Exception) -> bool:
        return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429

    @staticmethod
    def collect_unique_keys() -> list[str]:
        keys: list[str] = []
        seen: set[str] = set()
        for key in [settings.gemini_api_key_primary, settings.gemini_api_key_secondary]:
            cleaned = (key or "").strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                keys.append(cleaned)
        for key in (settings.gemini_api_keys or "").split(","):
            cleaned = key.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                keys.append(cleaned)
        return keys

    def has_configured_keys(self) -> bool:
        return bool(self.collect_unique_keys())

    def get_available_keys(self) -> list[str]:
        now_utc = datetime.now(timezone.utc)
        with self._lock:
            self._exhausted_until = {
                key: until for key, until in self._exhausted_until.items() if until > now_utc
            }
            keys = self.collect_unique_keys()
            available = [key for key in keys if key not in self._exhausted_until]
            if not available:
                return []
            start = self._cursor % len(available)
            rotated = available[start:] + available[:start]
            self._cursor = (self._cursor + 1) % len(available)
            return rotated

    def mark_exhausted_today(self, key: str) -> None:
        with self._lock:
            self._exhausted_until[key] = self._local_day_end_utc()


GEMINI_KEY_POOL = GeminiKeyPool()


def generate_content(
    *,
    user_text: str,
    api_key: str,
    use_maps_grounding: bool = False,
    language_code: str = "en_US",
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Call Gemini generateContent; returns raw API JSON."""
    if not api_key:
        raise ValueError("Gemini API key is missing.")

    url = GEMINI_API_URL_TEMPLATE.format(model=settings.gemini_model, api_key=api_key)
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
    }
    if use_maps_grounding:
        payload["tools"] = [{"googleMaps": {"enableWidget": False}}]
        payload["toolConfig"] = {
            "retrievalConfig": {
                "latLng": {"latitude": KV_GROUNDING_LAT, "longitude": KV_GROUNDING_LON},
                "languageCode": language_code,
            }
        }

    response = httpx.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def extract_text_from_response(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini response has no candidates.")
    parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    answer = "\n".join(text_parts).strip()
    if not answer:
        raise ValueError("Gemini response text is empty.")
    return answer


def extract_grounding_places(data: dict[str, Any], *, limit: int = 3) -> list[dict[str, str]]:
    """Parse groundingChunks from Gemini Maps grounding metadata."""
    candidates = data.get("candidates") or []
    if not candidates:
        return []
    metadata = (candidates[0] or {}).get("groundingMetadata") or {}
    chunks = metadata.get("groundingChunks") or []
    places: list[dict[str, str]] = []
    seen: set[str] = set()
    for chunk in chunks:
        maps_data = chunk.get("maps") or {}
        title = (maps_data.get("title") or "").strip()
        uri = (maps_data.get("uri") or "").strip()
        place_id = (maps_data.get("placeId") or "").strip()
        key = place_id or uri or title
        if not title or not key or key in seen:
            continue
        seen.add(key)
        places.append({"title": title, "url": uri, "place_id": place_id})
        if len(places) >= limit:
            break
    return places


async def call_with_key_pool(
    build_prompt: str,
    *,
    use_maps_grounding: bool = False,
    language_code: str = "en_US",
    timeout: float = 20.0,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Try each available API key. Returns (response_json, error_kind).
    error_kind: 'quota_exhausted' | 'unavailable' | None
    """
    keys = GEMINI_KEY_POOL.get_available_keys()
    if not keys:
        if GEMINI_KEY_POOL.has_configured_keys():
            return None, "quota_exhausted"
        return None, "unavailable"

    rate_limit_count = 0
    for key in keys:
        try:
            started = time.perf_counter()
            data = generate_content(
                user_text=build_prompt,
                api_key=key,
                use_maps_grounding=use_maps_grounding,
                language_code=language_code,
                timeout=timeout,
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            data["_eldergo_meta"] = {
                "latency_ms": elapsed_ms,
                "maps_grounding": use_maps_grounding,
            }
            return data, None
        except Exception as exc:
            if GeminiKeyPool.is_rate_limit_error(exc):
                rate_limit_count += 1
                GEMINI_KEY_POOL.mark_exhausted_today(key)
            continue

    if rate_limit_count > 0 and rate_limit_count >= len(GEMINI_KEY_POOL.collect_unique_keys()):
        return None, "quota_exhausted"
    return None, "unavailable"


def parse_json_from_text(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
