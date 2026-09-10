# app/schemas/routine.py
from typing import List, Optional
from pydantic import BaseModel


class RoutineBase(BaseModel):
    routine_id: str
    source_doc_id: Optional[str] = None
    source_url: Optional[str] = None

    title: str
    goal: Optional[str] = None
    description: Optional[str] = None

    target_emotions: List[str] = []
    target_situations: List[str] = []

    routine_type: Optional[str] = None
    difficulty: Optional[str] = None
    duration_min: Optional[int] = None
    environment: List[str] = []
    required_tools: List[str] = []

    steps: List[str]
    safety_notes: List[str] = []

    tags: List[str] = []
    language: str = "ko"


class Routine(RoutineBase):
    """API 응답용"""
    pass


class RoutineCreate(RoutineBase):
    """루틴 생성 로직/스크립트용"""
    pass
