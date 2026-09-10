# app/schemas/chat_session.py

from uuid import UUID
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class InputItem(BaseModel):
    id: UUID
    session_id: UUID
    created_at: datetime
    input_type: str          # "TEXT" 만 사용 중이지만 확장 대비
    text_content: Optional[str] = None

    class Config:
        orm_mode = True


class ChatSessionSummary(BaseModel):
    id: UUID
    start_time: datetime
    # 나중에 summary/title 추가 가능
    # summary: Optional[str] = None

    class Config:
        orm_mode = True


class ChatSessionDetail(BaseModel):
    id: UUID
    start_time: datetime
    inputs: List[InputItem]

    class Config:
        orm_mode = True
