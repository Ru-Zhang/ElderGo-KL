import { apiRequest } from './api';
import { ApiTravelPreferences, TravelPreferences, fromApiPreferences, toApiPreferences } from '../types/preferences';
import { ApiUISettings, UISettings, fromApiSettings, toApiSettings } from '../types/settings';

interface AnonymousUserResponse {
  anonymous_user_id: string;
}

export async function createAnonymousUser(deviceId: string): Promise<string> {
  // Device id is resolved server-side into a stable anonymous UUID.
  const response = await apiRequest<AnonymousUserResponse>('/users/anonymous', {
    method: 'POST',
    body: JSON.stringify({ device_id: deviceId })
  });
  return response.anonymous_user_id;
}

export async function getUISettings(anonymousUserId: string): Promise<UISettings> {
  // Convert API shape to frontend shape at the boundary.
  return fromApiSettings(await apiRequest<ApiUISettings>(`/users/${anonymousUserId}/ui-settings`));
}

export async function updateUISettings(anonymousUserId: string, settings: UISettings): Promise<UISettings> {
  return fromApiSettings(await apiRequest<ApiUISettings>(`/users/${anonymousUserId}/ui-settings`, {
    method: 'PATCH',
    body: JSON.stringify(toApiSettings(settings))
  }));
}

export async function getTravelPreferences(anonymousUserId: string): Promise<TravelPreferences> {
  return fromApiPreferences(await apiRequest<ApiTravelPreferences>(`/users/${anonymousUserId}/travel-preferences`));
}

export async function updateTravelPreferences(
  anonymousUserId: string,
  preferences: TravelPreferences
): Promise<TravelPreferences> {
  return fromApiPreferences(await apiRequest<ApiTravelPreferences>(`/users/${anonymousUserId}/travel-preferences`, {
    method: 'PATCH',
    body: JSON.stringify(toApiPreferences(preferences))
  }));
}
