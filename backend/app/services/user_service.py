from __future__ import annotations

from hashlib import sha256
from uuid import NAMESPACE_URL
from uuid import UUID
from uuid import uuid5

from app.core.config import get_settings
from app.schemas.preferences import TravelPreferences
from app.schemas.settings import UISettings
from app.services.database import get_connection

settings = get_settings()

_demo_ui_settings: dict[str, UISettings] = {}
_demo_travel_preferences: dict[str, TravelPreferences] = {}


def _device_hash(device_id: str) -> str:
    return sha256(device_id.encode("utf-8")).hexdigest()


def _parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def _db_language_to_api(value: str | None) -> str:
    if value == "ms":
        return "BM"
    return "EN"


def _api_language_to_db(value: str) -> str:
    if value == "BM":
        return "ms"
    return "en"


def _ensure_default_user_rows(conn, anonymous_user_id: str) -> None:
    conn.execute(
        """
        INSERT INTO user_ui_settings (
            anonymous_user_id,
            language_code,
            font_size_mode,
            onboarding_completed,
            updated_at
        )
        VALUES (%(anonymous_user_id)s::uuid, 'en', 'standard', FALSE, CURRENT_TIMESTAMP)
        ON CONFLICT (anonymous_user_id) DO NOTHING
        """,
        {"anonymous_user_id": anonymous_user_id},
    )
    conn.execute(
        """
        INSERT INTO user_travel_preferences (
            anonymous_user_id,
            accessibility_first,
            less_walking,
            fewer_transfers,
            updated_at
        )
        VALUES (%(anonymous_user_id)s::uuid, FALSE, FALSE, FALSE, CURRENT_TIMESTAMP)
        ON CONFLICT (anonymous_user_id) DO NOTHING
        """,
        {"anonymous_user_id": anonymous_user_id},
    )


def create_or_resolve_anonymous_user(device_id: str) -> str:
    if settings.demo_mode:
        anonymous_user_id = str(uuid5(NAMESPACE_URL, _device_hash(device_id)))
        _demo_ui_settings.setdefault(anonymous_user_id, UISettings())
        _demo_travel_preferences.setdefault(anonymous_user_id, TravelPreferences())
        return anonymous_user_id

    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO anonymous_users (
                device_id_hash,
                last_seen_at
            )
            VALUES (%(device_id_hash)s, CURRENT_TIMESTAMP)
            ON CONFLICT (device_id_hash) DO UPDATE SET
                last_seen_at = CURRENT_TIMESTAMP
            RETURNING anonymous_user_id::text AS anonymous_user_id
            """,
            {"device_id_hash": _device_hash(device_id)},
        ).fetchone()
        anonymous_user_id = row["anonymous_user_id"]
        _ensure_default_user_rows(conn, anonymous_user_id)
        return anonymous_user_id


def get_ui_settings(anonymous_user_id: str) -> UISettings:
    if settings.demo_mode:
        return _demo_ui_settings.setdefault(anonymous_user_id, UISettings())

    if _parse_uuid(anonymous_user_id) is None:
        return UISettings()

    with get_connection() as conn:
        _ensure_default_user_rows(conn, anonymous_user_id)
        row = conn.execute(
            """
            SELECT language_code, font_size_mode, onboarding_completed
            FROM user_ui_settings
            WHERE anonymous_user_id = %(anonymous_user_id)s::uuid
            """,
            {"anonymous_user_id": anonymous_user_id},
        ).fetchone()
        if row is None:
            return UISettings()
        return UISettings(
            language=_db_language_to_api(row["language_code"]),
            font_size=row["font_size_mode"] or "standard",
            onboarding_completed=bool(row["onboarding_completed"]),
        )


def update_ui_settings(anonymous_user_id: str, payload: UISettings) -> UISettings:
    if settings.demo_mode:
        _demo_ui_settings[anonymous_user_id] = payload
        return payload

    if _parse_uuid(anonymous_user_id) is None:
        return payload

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_ui_settings (
                anonymous_user_id,
                language_code,
                font_size_mode,
                onboarding_completed,
                updated_at
            )
            VALUES (
                %(anonymous_user_id)s::uuid,
                %(language_code)s,
                %(font_size_mode)s,
                %(onboarding_completed)s,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (anonymous_user_id) DO UPDATE SET
                language_code = EXCLUDED.language_code,
                font_size_mode = EXCLUDED.font_size_mode,
                onboarding_completed = EXCLUDED.onboarding_completed,
                updated_at = CURRENT_TIMESTAMP
            """,
            {
                "anonymous_user_id": anonymous_user_id,
                "language_code": _api_language_to_db(payload.language),
                "font_size_mode": payload.font_size,
                "onboarding_completed": payload.onboarding_completed,
            },
        )
    return payload


def get_travel_preferences(anonymous_user_id: str) -> TravelPreferences:
    if settings.demo_mode:
        return _demo_travel_preferences.setdefault(anonymous_user_id, TravelPreferences())

    if _parse_uuid(anonymous_user_id) is None:
        return TravelPreferences()

    with get_connection() as conn:
        _ensure_default_user_rows(conn, anonymous_user_id)
        row = conn.execute(
            """
            SELECT accessibility_first, less_walking, fewer_transfers
            FROM user_travel_preferences
            WHERE anonymous_user_id = %(anonymous_user_id)s::uuid
            """,
            {"anonymous_user_id": anonymous_user_id},
        ).fetchone()
        if row is None:
            return TravelPreferences()
        return TravelPreferences(
            accessibility_first=bool(row["accessibility_first"]),
            least_walk=bool(row["less_walking"]),
            fewest_transfers=bool(row["fewer_transfers"]),
        )


def update_travel_preferences(
    anonymous_user_id: str,
    payload: TravelPreferences,
) -> TravelPreferences:
    if settings.demo_mode:
        _demo_travel_preferences[anonymous_user_id] = payload
        return payload

    if _parse_uuid(anonymous_user_id) is None:
        return payload

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_travel_preferences (
                anonymous_user_id,
                accessibility_first,
                less_walking,
                fewer_transfers,
                updated_at
            )
            VALUES (
                %(anonymous_user_id)s::uuid,
                %(accessibility_first)s,
                %(less_walking)s,
                %(fewer_transfers)s,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (anonymous_user_id) DO UPDATE SET
                accessibility_first = EXCLUDED.accessibility_first,
                less_walking = EXCLUDED.less_walking,
                fewer_transfers = EXCLUDED.fewer_transfers,
                updated_at = CURRENT_TIMESTAMP
            """,
            {
                "anonymous_user_id": anonymous_user_id,
                "accessibility_first": payload.accessibility_first,
                "less_walking": payload.least_walk,
                "fewer_transfers": payload.fewest_transfers,
            },
        )
    return payload
