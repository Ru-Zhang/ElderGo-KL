export type LanguageCode = 'EN' | 'BM';
export type FontSizeMode = 'standard' | 'large' | 'extra_large';

export interface UISettings {
  language: LanguageCode;
  fontSize: FontSizeMode;
  onboardingCompleted: boolean;
}

export interface ApiUISettings {
  language: LanguageCode;
  font_size: FontSizeMode;
  onboarding_completed: boolean;
}

export function toApiSettings(settings: UISettings): ApiUISettings {
  return {
    language: settings.language,
    font_size: settings.fontSize,
    onboarding_completed: settings.onboardingCompleted
  };
}

export function fromApiSettings(settings: ApiUISettings): UISettings {
  // Normalize backend naming for app context consumption.
  return {
    language: settings.language,
    fontSize: settings.font_size,
    onboardingCompleted: settings.onboarding_completed
  };
}
