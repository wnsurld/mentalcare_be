from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Dict, List

class SessionReportList(BaseModel):
    report_id: UUID
    session_id: UUID
    created_at: datetime
    highlights:str



class WeeklyReportList(BaseModel):
    weekly_id: UUID
    week_start_date: date
    week_info: str


class SessionReportDetail(BaseModel):
    report_id: UUID
    session_id: UUID
    summary: Dict
    highlights: str
    mood_overview: str
    routine_overview: Dict
    created_at: datetime


class WeeklyReportDetail(BaseModel):
    weekly_id: UUID
    user_id: UUID
    week_info: str
    mood_distribution: List[Dict]
    weekly_mood_analysis: Dict
    mood_manage_tip: str
    positive_highlights: str
    routine_overview: List[Dict]
