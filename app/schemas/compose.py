from pydantic import BaseModel
from typing import Dict, Any


class ComposeRequest(BaseModel):
    routine_draft: Dict[str, Any]
    user_profile: Dict[str, Any] | None = None


class ComposeResponse(BaseModel):
    message: str
    card: Dict[str, Any]