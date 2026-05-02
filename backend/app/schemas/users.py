from pydantic import BaseModel, Field


class AnonymousUserCreate(BaseModel):
    # Minimum length filters obviously invalid transient ids from clients.
    device_id: str = Field(min_length=8)


class AnonymousUserResponse(BaseModel):
    anonymous_user_id: str
