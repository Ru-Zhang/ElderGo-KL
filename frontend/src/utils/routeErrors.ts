import { ApiError } from '../services/api';
import type { TranslationKey } from '../i18n/translations';

const API_ERROR_KEYS: Partial<Record<string, TranslationKey>> = {
  no_transit_route: 'routeNoTransitAtTime',
  request_timeout: 'apiRequestTimeout',
};

export function isNoTransitError(error: unknown): boolean {
  return error instanceof ApiError && error.code === 'no_transit_route';
}

export function resolveRouteErrorMessage(
  error: unknown,
  t: (key: TranslationKey) => string,
  fallbackKey: TranslationKey = 'planTimeUnableToRoute',
): string {
  if (error instanceof ApiError && error.code && API_ERROR_KEYS[error.code]) {
    return t(API_ERROR_KEYS[error.code]!);
  }
  return t(fallbackKey);
}
