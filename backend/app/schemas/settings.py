from typing import Literal

from pydantic import BaseModel


LanguageCode = Literal["EN", "BM"]
FontSizeMode = Literal["standard", "large", "extra_large"]


class UISettings(BaseModel):
    # Defaults keep first-launch UX predictable before remote profile restore.
    language: LanguageCode = "EN"
    font_size: FontSizeMode = "standard"
    onboarding_completed: bool = False
