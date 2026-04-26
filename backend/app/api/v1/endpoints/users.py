from hashlib import sha256

from fastapi import APIRouter

from app.schemas.preferences import TravelPreferences
from app.schemas.settings import UISettings
from app.schemas.users import AnonymousUserCreate, AnonymousUserResponse

router = APIRouter()

_settings_cache: dict[str, UISettings] = {}
_preferences_cache: dict[str, TravelPreferences] = {}


def _anonymous_id(device_id: str) -> str:
    return f"anon_{sha256(device_id.encode('utf-8')).hexdigest()[:24]}"


@router.post("/anonymous", response_model=AnonymousUserResponse)
def create_anonymous_user(payload: AnonymousUserCreate) -> AnonymousUserResponse:
    anonymous_user_id = _anonymous_id(payload.device_id)
    _settings_cache.setdefault(anonymous_user_id, UISettings())
    _preferences_cache.setdefault(anonymous_user_id, TravelPreferences())
    return AnonymousUserResponse(anonymous_user_id=anonymous_user_id)


@router.get("/{anonymous_user_id}/ui-settings", response_model=UISettings)
def get_ui_settings(anonymous_user_id: str) -> UISettings:
    return _settings_cache.setdefault(anonymous_user_id, UISettings())


@router.patch("/{anonymous_user_id}/ui-settings", response_model=UISettings)
def update_ui_settings(anonymous_user_id: str, payload: UISettings) -> UISettings:
    _settings_cache[anonymous_user_id] = payload
    return payload


@router.get("/{anonymous_user_id}/travel-preferences", response_model=TravelPreferences)
def get_travel_preferences(anonymous_user_id: str) -> TravelPreferences:
    return _preferences_cache.setdefault(anonymous_user_id, TravelPreferences())


@router.patch("/{anonymous_user_id}/travel-preferences", response_model=TravelPreferences)
def update_travel_preferences(
    anonymous_user_id: str,
    payload: TravelPreferences,
) -> TravelPreferences:
    _preferences_cache[anonymous_user_id] = payload
    return payload
