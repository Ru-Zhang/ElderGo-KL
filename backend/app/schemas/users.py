from pydantic import BaseModel, Field


class AnonymousUserCreate(BaseModel):
    device_id: str = Field(min_length=8)


class AnonymousUserResponse(BaseModel):
    anonymous_user_id: str
