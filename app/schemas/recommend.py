# app/schemas/recommend.py
from pydantic import BaseModel, Field
from typing import List


class RoutineRecommendRequest(BaseModel):
    text: str = Field(..., description="사용자가 입력한 상황/감정 텍스트")
    limit: int = Field(5, ge=1, le=20, description="추천 루틴 개수")


class RoutineRecommendItem(BaseModel):
    routine_id: str
    title: str
    description: str
    score: float


class RoutineRecommendResponse(BaseModel):
    routines: List[RoutineRecommendItem]
