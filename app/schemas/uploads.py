# app/schemas/uploads.py

from typing import Optional, Dict, Any
from uuid import UUID
from app.models.enum import InputType

from pydantic import BaseModel

# ✅ 요청 스키마: 텍스트 업로드
class UploadTextRequest(BaseModel):
    text: str
    # 첫 메시지면 session_id 없이 보내도 됨 → 백엔드가 새 세션 생성
    session_id: Optional[UUID] = None
    meta: Optional[Dict[str, Any]] = None


# ✅ 응답 스키마
class UploadResponse(BaseModel):
    input_id: UUID
    session_id: UUID
    input_type: InputType   # ← 이미 쓰고 있는 enum 재사용
    text: Optional[str] = None
