# app/schemas/user.py
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

from uuid import UUID

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    name: str | None = None
    locale: str | None = None

    model_config = ConfigDict(from_attributes=True)

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
