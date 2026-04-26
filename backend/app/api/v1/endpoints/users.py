from fastapi import APIRouter

from app.schemas.preferences import TravelPreferences
from app.schemas.settings import UISettings
from app.schemas.users import AnonymousUserCreate, AnonymousUserResponse
from app.services.user_service import (
    create_or_resolve_anonymous_user,
    get_travel_preferences as get_travel_preferences_service,
    get_ui_settings as get_ui_settings_service,
    update_travel_preferences as update_travel_preferences_service,
    update_ui_settings as update_ui_settings_service,
)

router = APIRouter()


@router.post("/anonymous", response_model=AnonymousUserResponse)
def create_anonymous_user(payload: AnonymousUserCreate) -> AnonymousUserResponse:
    anonymous_user_id = create_or_resolve_anonymous_user(payload.device_id)
    return AnonymousUserResponse(anonymous_user_id=anonymous_user_id)


@router.get("/{anonymous_user_id}/ui-settings", response_model=UISettings)
def get_ui_settings(anonymous_user_id: str) -> UISettings:
    return get_ui_settings_service(anonymous_user_id)


@router.patch("/{anonymous_user_id}/ui-settings", response_model=UISettings)
def update_ui_settings(anonymous_user_id: str, payload: UISettings) -> UISettings:
    return update_ui_settings_service(anonymous_user_id, payload)


@router.get("/{anonymous_user_id}/travel-preferences", response_model=TravelPreferences)
def get_travel_preferences(anonymous_user_id: str) -> TravelPreferences:
    return get_travel_preferences_service(anonymous_user_id)


@router.patch("/{anonymous_user_id}/travel-preferences", response_model=TravelPreferences)
def update_travel_preferences(
    anonymous_user_id: str,
    payload: TravelPreferences,
) -> TravelPreferences:
    return update_travel_preferences_service(anonymous_user_id, payload)
