from pydantic import BaseModel
from typing import List, Dict, Any


class AggregateRequest(BaseModel):
    docs: List[Dict[str, Any]]


class Situation(BaseModel):
    label: str
    evidence: List[str] | None = None


class RoutineDraft(BaseModel):
    title: str
    duration_min: int
    steps: List[str]
    why: str | None = None


class AggregateResponse(BaseModel):
    situation: Situation
    routine_draft: RoutineDraft